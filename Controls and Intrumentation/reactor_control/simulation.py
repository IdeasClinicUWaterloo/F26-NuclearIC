import numpy as np
from scipy.integrate import solve_ivp

from model import ReactorModel
from ekf import EKF
from state_machine import SafetySupervisor
from fault_monitor import FaultMonitor
from plotting import plot_simulation


class Simulation:
    def __init__(self, duration=200.0, dt=0.1, desired_n=1.0):
        self.model = ReactorModel()
        self.duration = duration
        self.dt = dt
        self.desired_n = desired_n

        self.feedback_rho_values = [] # Thermal reactivity values at each time step

        self.time_steps = [] # Times at which the state is recorded
        self.control_times = [] # Times at which control actions are taken
        self.control_values = [] # Control-rod reactivity values at each control time
        self.n_current_values = [] # Current neutron population values at each time step
        self.n_desired_values = [] # Desired neutron population values at each time step
        self.n_measured_values = [] # Raw noisy power readings at each time step
        self.n_estimated_values = [] # EKF-filtered power estimate at each time step
        self.commanded_rho_values = [] # What the controller asked for, before safety/actuator overrides
        self.safety_states = [] # Safety supervisor state at each control time
        self.fuel_temp_values = [] # True fuel temperature at each time step
        self.coolant_temp_avg_values = [] # True average coolant temperature at each time step
        self.fault_flag_history = [] # dict of {channel: bool} at each control time
        self.disturbance_suspected_history = [] # bool at each control time
        self.safety = None # SafetySupervisor from the most recent simulate() run

    def _build_safety_supervisor(self):
        """Sets up the safety supervisor with warn/limit/scram thresholds
        for power, fuel temperature, and coolant temperature, based on
        margins above/below this reactor's steady-state operating point."""

        limits = {
            "power": {"warn": 1.05, "limit": 1.10, "scram": 1.25},
            "fuel_temp": {
                "warn": self.model.T_fuel0 + 20,
                "limit": self.model.T_fuel0 + 40,
                "scram": self.model.T_fuel0 + 90,
            },
            "coolant_temp": {
                "warn": self.model.T_cref + 15,
                "limit": self.model.T_cref + 25,
                "scram": self.model.T_cref + 50,
            },
        }

        return SafetySupervisor(
            limits=limits,
            rho_min=-5e-4,
            rho_max=5e-4,
            limiting_rho_max=0.0,
        )

    def _apply_actuator_fault(self, commanded_rho, rod_history, t, actuator_fault):
        """Models a real actuator diverging from what it was told to do.
        actuator_fault is None (no fault) or a dict:
          {"type": "stuck", "t_start": <s>, "value": <optional fixed rho>}
          {"type": "delay", "t_start": <s>, "lag_steps": <int>}
        """

        if actuator_fault is None or t < actuator_fault.get("t_start", 0.0):
            return commanded_rho

        if actuator_fault["type"] == "stuck":
            return actuator_fault.get("value", rod_history[-1] if rod_history else 0.0)

        if actuator_fault["type"] == "delay":
            lag = actuator_fault.get("lag_steps", 10)
            idx = len(rod_history) - lag
            return rod_history[idx] if idx >= 0 else rod_history[0] if rod_history else 0.0

        return commanded_rho

    def _build_ekf(self, current_state, sensor_suite):
        """Sets up the EKF that estimates the full reactor state
        (n, precursors, fuel/coolant temps) from the noisy sensors."""

        n_states = current_state.shape[0]

        # Which state entries are directly measured: n (0), T_fuel (7),
        # T_c1 (8), T_c2 (9).
        H = np.zeros((4, n_states))
        H[0, 0] = 1.0
        H[1, 7] = 1.0
        H[2, 8] = 1.0
        H[3, 9] = 1.0

        R = np.diag([
            sensor_suite.power.sigma ** 2,
            sensor_suite.fuel_temp.sigma ** 2,
            sensor_suite.coolant_temp_1.sigma ** 2,
            sensor_suite.coolant_temp_2.sigma ** 2,
        ])

        # Starting guess for process noise -- how much to trust the model
        # vs. the measurements for each state. Tune these.
        Q = np.diag([1e-5] + [1e-8] * 6 + [1e-2, 1e-2, 1e-2])

        # Starting uncertainty in the initial estimate.
        P0 = np.diag([1e-4] + [1e-6] * 6 + [1.0, 1.0, 1.0])

        x0_est = current_state.copy()

        return EKF(
            model=self.model,
            H=H, Q=Q, R=R, x0=x0_est, P0=P0, dt=self.dt,
        )

    def simulate(self, controller, sensor_suite, use_filter=True, actuator_fault=None):
        """
        Simulates the reactor's neutron population.
        First, takes the current n from the state vector,
        places current and desired inside arrays, and then
        simulates for a number of steps.

        Takes rho from control and gives it to the model,
        and appends control values, then solves the ODEs.

        Appends the current n values so plot() can use them.

        If use_filter is True, the controller sees the EKF's filtered power
        estimate instead of the raw noisy sensor reading.

        actuator_fault (optional) models a rod actuator that doesn't do what
        it's told -- see _apply_actuator_fault for the supported dict shapes.
        """

        current_state = self.model.x0.copy()
        number_of_steps = int(self.duration / self.dt)

        ekf = self._build_ekf(current_state, sensor_suite)
        self.safety = self._build_safety_supervisor()
        fault_monitor = FaultMonitor(
            channel_names=["power", "fuel_temp", "coolant_1_temp", "coolant_2_temp"]
        )

        self.time_steps = [0.0]
        self.n_current_values = [current_state[0]]
        self.n_desired_values = [self.desired_n]
        self.n_measured_values = [current_state[0]]
        self.n_estimated_values = [ekf.x[0]]
        self.control_times = []
        self.control_values = []
        self.commanded_rho_values = []
        self.safety_states = []
        self.fuel_temp_values = [current_state[7]]
        self.coolant_temp_avg_values = [0.5 * (current_state[8] + current_state[9])]
        self.fault_flag_history = []
        self.disturbance_suspected_history = []

        for i in range(number_of_steps):
            t = i * self.dt

            sensor_suite.step(self.dt)
            readings = sensor_suite.read_all(current_state, self.model.rho_rod)

            z = np.array([
                readings["power"],
                readings["fuel_temp"],
                readings["coolant_1_temp"],
                readings["coolant_2_temp"],
            ])

            # A dropped-out sensor reads NaN -- skip the update this step
            # and let the estimate coast on the model (predict-only) rather
            # than poisoning the whole state estimate with NaNs.
            if not np.any(np.isnan(z)):
                ekf.update(z)
                fault_flags = fault_monitor.update(ekf.normalized_innovation())
            else:
                fault_flags = dict(fault_monitor.flagged)

            self.fault_flag_history.append(fault_flags)
            self.disturbance_suspected_history.append(fault_monitor.disturbance_suspected)

            current_n = ekf.x[0] if use_filter else readings["power"]

            commanded_rho = controller.update(self.desired_n, current_n, self.dt)
            self.commanded_rho_values.append(commanded_rho)

            coolant_avg_reading = 0.5 * (readings["coolant_1_temp"] + readings["coolant_2_temp"])
            safety_state = self.safety.evaluate({
                "power": readings["power"],
                "fuel_temp": readings["fuel_temp"],
                "coolant_temp": coolant_avg_reading,
            })
            self.safety_states.append(safety_state)

            safe_rho = self.safety.apply(commanded_rho)
            actual_rho = self._apply_actuator_fault(safe_rho, self.control_values, t, actuator_fault)

            self.model.rho_rod = actual_rho
            self.control_times.append(t)
            self.control_values.append(actual_rho)

            sol = solve_ivp(
                fun=self.model.dynamics,
                t_span=(t, t + self.dt),
                y0=current_state,
                t_eval=[t + self.dt],
                method="Radau",
            )
            if not sol.success:
                raise RuntimeError(sol.message)

            current_state = sol.y[:, -1]

            # Predict the estimate forward to t + dt using the same rod
            # command applied to the true system, ready for the next
            # iteration's update.
            ekf.predict(self.model.rho_rod)

            self.time_steps.append(t + self.dt)
            self.n_current_values.append(current_state[0])
            self.n_desired_values.append(self.desired_n)
            self.n_measured_values.append(readings["power"])
            self.n_estimated_values.append(ekf.x[0])
            self.fuel_temp_values.append(current_state[7])
            self.coolant_temp_avg_values.append(0.5 * (current_state[8] + current_state[9]))

            self.feedback_rho_values.append(self.model.rho_feedback(current_state[7],
                    0.5 * (current_state[8] + current_state[9])))

        return current_state

    def plot(self):
        plot_simulation(self)


if __name__ == "__main__":
    from control import Controller
    from sensors import SensorSuite

    controller = Controller(kp=1e-4, ki=0, kd=0)
    simulator = Simulation(duration=200.0, dt=0.1, desired_n=1.0)
    sensor_suite = SensorSuite()
    final_state = simulator.simulate(controller, sensor_suite)

    print("Initial temperatures:")
    print(f"T_fuel0 = {simulator.model.T_fuel0:.2f} K")
    print(f"T_c1_0  = {simulator.model.T_c1_0:.2f} K")
    print(f"T_c2_0  = {simulator.model.T_c2_0:.2f} K")
    print(f"T_cref  = {simulator.model.T_cref:.2f} K")
    print(f"Final normalized power = {final_state[0]:.6f}")

    simulator.plot()
