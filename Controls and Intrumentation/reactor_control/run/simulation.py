"""Closed-loop simulation: wires the reactor model, sensors, controller,
state estimator, and safety supervisor together and steps them in time."""

import numpy as np
from scipy.integrate import solve_ivp

from reactor.model import ReactorModel
from estimation.ekf import EKF
from controller.control import MAX_ROD_SPEED
from controller.state_machine import SafetySupervisor
from run.plotting import plot_simulation

# Measurement channels, in the order the EKF expects them.
CHANNELS = ["power", "fuel_temp", "coolant_1_temp", "coolant_2_temp"]

# How far the rods can travel, in reactivity. Fully inserted to fully
# withdrawn is ROD_MIN to ROD_MAX.
ROD_MIN, ROD_MAX = -5e-4, 5e-4


class Simulation:
    def __init__(self, duration=200.0, dt=0.1, desired_n=1.0):
        self.model = ReactorModel()
        self.duration = duration
        self.dt = dt
        self.desired_n = desired_n

        self.safety = None  # SafetySupervisor from the most recent run
        self._clear_history()

    def _clear_history(self):
        """Empties every recorded trace. Called at the top of simulate() so
        re-running the same Simulation starts clean instead of appending
        onto the previous run's data."""

        # Sampled once per timestep, including the initial state at t=0.
        self.time_steps = []
        self.n_current_values = []          # true neutron population
        self.n_desired_values = []          # setpoint
        self.n_measured_values = []         # raw noisy power reading
        self.n_estimated_values = []        # EKF power estimate
        self.fuel_temp_values = []          # true fuel temperature
        self.coolant_temp_avg_values = []   # true average coolant temperature
        self.feedback_rho_values = []       # thermal reactivity feedback

        # Sampled once per control action, so one entry shorter than above.
        self.control_times = []
        self.control_values = []            # rho actually applied to the reactor
        self.commanded_rho_values = []      # rho the controller asked for
        self.safety_states = []

    def _build_safety_supervisor(self):
        """Sets the warn / limit / scram thresholds, each a margin above where
        this reactor normally sits when running happily."""

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
            rho_min=ROD_MIN,
            rho_max=ROD_MAX,
            limiting_rho_max=0.0,
        )

    def _build_ekf(self, current_state, sensor_suite):
        """Sets up the EKF that estimates the full reactor state
        (n, precursors, fuel/coolant temps) from the noisy sensors."""

        n_states = current_state.shape[0]

        # H says which of the 10 states each sensor actually reads. We measure
        # power (state 0) and the three temperatures (states 7, 8, 9). Nothing
        # measures the six precursor groups -- the filter works those out.
        H = np.zeros((4, n_states))
        H[0, 0] = 1.0
        H[1, 7] = 1.0
        H[2, 8] = 1.0
        H[3, 9] = 1.0

        # R says how noisy each sensor is, taken straight from the sensors
        # themselves. Noisier sensor, less the filter leans on it.
        R = np.diag([
            sensor_suite.power.sigma ** 2,
            sensor_suite.fuel_temp.sigma ** 2,
            sensor_suite.coolant_temp_1.sigma ** 2,
            sensor_suite.coolant_temp_2.sigma ** 2,
        ])

        # Q says how much the filter is allowed to doubt its own model. Bigger
        # Q means "my model might be wrong, listen to the sensors more".
        #
        # Each state gets its own value, because they are wildly different
        # sizes: power sits around 1, while the precursor groups run from
        # about 2 up to about 950. A single number that suits one will be
        # hopeless for the other, so the precursors get a value scaled to how
        # big they actually are.
        #
        # This matters more than it looks. The filter's model does not know
        # about the disturbances the scenarios inject -- that is the whole
        # point of calling them disturbances. So when one hits, the filter has
        # to explain the extra reactivity somehow, and the precursors are the
        # sensible place for it to go. If you pin them down with a tiny Q
        # instead, the filter cannot adjust them, so it argues with every
        # measurement that disagrees with its model. The power estimate then
        # ends up further off than the raw sensor was -- worse than useless.
        # Try setting q_precursor_relative to 1e-5 and watch it happen.
        q_power = 1e-5               # power is around 1, so a plain value is fine
        q_precursor_relative = 1e-2  # 1% of each precursor's own size
        q_temp = 1e-2                # temperatures, in K^2

        Q = np.diag(
            [q_power]
            + [(q_precursor_relative * c) ** 2 for c in self.model.C0]
            + [q_temp] * 3
        )

        # Uncertainty in the initial estimate.
        P0 = np.diag([1e-4] + [1e-6] * 6 + [1.0, 1.0, 1.0])

        return EKF(
            model=self.model,
            H=H, Q=Q, R=R, x0=current_state.copy(), P0=P0, dt=self.dt,
        )

    def _apply_actuator_fault(self, commanded_rho, commanded_history,
                              applied_history, t, actuator_fault):
        """Models a rod drive that doesn't do what it's told.

        actuator_fault is None, or a dict:
          {"type": "stuck", "t_start": <s>, "value": <optional fixed rho>}
          {"type": "delay", "t_start": <s>, "lag_steps": <int>}

        The two histories are not interchangeable. A stuck rod is frozen where
        it actually got to, so it looks at what was applied. A slow rod is
        still working through the queue of orders it was given, so it looks at
        what was commanded. Point the slow one at its own past output instead
        and it just repeats its first move forever, never going anywhere.
        """

        if actuator_fault is None or t < actuator_fault.get("t_start", 0.0):
            return commanded_rho

        if actuator_fault["type"] == "stuck":
            if "value" in actuator_fault:
                return actuator_fault["value"]
            return applied_history[-1] if applied_history else 0.0

        if actuator_fault["type"] == "delay":
            # commanded_history holds the orders issued *before* this step, so
            # [-lag] is exactly lag steps back. Until that many have piled up
            # the rod is still sitting where it started.
            lag = actuator_fault.get("lag_steps", 10)
            if len(commanded_history) < lag:
                return 0.0
            return commanded_history[-lag]

        return commanded_rho

    def simulate(self, controller, sensor_suite, use_filter=True, actuator_fault=None):
        """Runs the closed loop for `duration` seconds and returns the final
        reactor state.

        Each timestep: read the sensors, update the estimate, ask the
        controller for a rod command, let the safety supervisor veto or
        clamp it, apply any actuator fault, then integrate the reactor
        forward with whatever rod reactivity actually got through.

        use_filter     -- controller sees the EKF estimate (True) or the raw
                          noisy power reading (False).
        actuator_fault -- see _apply_actuator_fault.
        """

        current_state = self.model.x0.copy()
        number_of_steps = int(self.duration / self.dt)

        # Rods start fully out of the way. Reset explicitly so a previous run
        # that ended in SCRAM doesn't leave its reactivity sitting here.
        rod_position = 0.0
        self.model.rho_rod = 0.0

        # What the actuator was told to do, step by step -- a lagging rod
        # works through this queue rather than its own past output.
        ordered_rho = []

        ekf = self._build_ekf(current_state, sensor_suite)
        self.safety = self._build_safety_supervisor()

        self._clear_history()
        self._record_state(0.0, current_state, measured_n=current_state[0],
                           estimated_n=ekf.x[0])

        for i in range(number_of_steps):
            t = i * self.dt

            sensor_suite.step(self.dt)
            readings = sensor_suite.read_all(current_state, self.model.rho_rod)
            z = np.array([readings[name] for name in CHANNELS])

            # A dead sensor reads NaN. Hand that to the filter and NaN spreads
            # into every value it tracks, wrecking all of them. But skipping
            # the step entirely throws away the sensors that are still fine,
            # so instead we update using only the working ones. Carrying on
            # through a dead sensor because the others still agree is much of
            # the reason for having four in the first place.
            healthy = ~np.isnan(z)
            if healthy.all():
                ekf.update(z)
            elif healthy.any():
                ekf.update(z[healthy],
                           H=ekf.H[healthy],
                           R=ekf.R[np.ix_(healthy, healthy)])

            current_n = ekf.x[0] if use_filter else readings["power"]

            # The controller asks for a rod speed; the drive motor's maximum
            # is physical, so enforce it here rather than trusting whatever
            # the controller returned. The rods then end up wherever they've
            # been driven to, within their travel limits.
            speed = controller.update(self.desired_n, current_n, self.dt)
            speed = np.clip(speed, -MAX_ROD_SPEED, MAX_ROD_SPEED)
            rod_position = np.clip(rod_position + speed * self.dt, ROD_MIN, ROD_MAX)
            commanded_rho = rod_position

            # The supervisor watches the raw instruments, deliberately not
            # the EKF -- a bug in the estimator must not disable safety.
            safety_state = self.safety.evaluate({
                "power": readings["power"],
                "fuel_temp": readings["fuel_temp"],
                "coolant_temp": 0.5 * (readings["coolant_1_temp"] + readings["coolant_2_temp"]),
            })
            safe_rho = self.safety.apply(commanded_rho)

            # If the supervisor merely clamped the rods, then that is genuinely
            # where they are, so keep the integrator in step -- otherwise it
            # winds up against a limit it cannot see. A SCRAM is different: it
            # drops separate, far heavier shutdown rods, and says nothing about
            # where the control rods ended up.
            if self.safety.state not in ("SCRAM", "SHUTDOWN"):
                rod_position = safe_rho

            actual_rho = self._apply_actuator_fault(
                safe_rho, ordered_rho, self.control_values, t, actuator_fault)
            ordered_rho.append(safe_rho)

            self.control_times.append(t)
            self.commanded_rho_values.append(commanded_rho)
            self.safety_states.append(safety_state)
            self.control_values.append(actual_rho)

            self.model.rho_rod = actual_rho
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

            # Push the estimate forward to t + dt with the same rod command
            # the real reactor got, ready for the next iteration's update.
            ekf.predict(self.model.rho_rod)

            self._record_state(t + self.dt, current_state,
                               measured_n=readings["power"], estimated_n=ekf.x[0])

        return current_state

    def _record_state(self, t, state, measured_n, estimated_n):
        """Appends one timestep's worth of data to the history traces."""

        coolant_avg = 0.5 * (state[8] + state[9])

        self.time_steps.append(t)
        self.n_current_values.append(state[0])
        self.n_desired_values.append(self.desired_n)
        self.n_measured_values.append(measured_n)
        self.n_estimated_values.append(estimated_n)
        self.fuel_temp_values.append(state[7])
        self.coolant_temp_avg_values.append(coolant_avg)
        self.feedback_rho_values.append(self.model.rho_feedback(state[7], coolant_avg))

    def plot(self):
        plot_simulation(self)


if __name__ == "__main__":
    # Run from the reactor_control folder with:  python -m run.simulation
    from controller.control import CONTROLLERS
    from reactor.sensors import SensorSuite

    controller = CONTROLLERS["pid"]()
    simulator = Simulation(duration=200.0, dt=0.1, desired_n=1.0)
    final_state = simulator.simulate(controller, SensorSuite())

    print("Initial temperatures:")
    print(f"T_fuel0 = {simulator.model.T_fuel0:.2f} K")
    print(f"T_c1_0  = {simulator.model.T_c1_0:.2f} K")
    print(f"T_c2_0  = {simulator.model.T_c2_0:.2f} K")
    print(f"T_cref  = {simulator.model.T_cref:.2f} K")
    print(f"Final normalized power = {final_state[0]:.6f}")

    simulator.plot()
