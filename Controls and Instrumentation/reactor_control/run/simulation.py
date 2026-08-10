"""Closed-loop reactor simulation and diagnostic history."""

import math
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
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError("duration must be a positive finite number")
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be a positive finite number")
        if not np.isfinite(desired_n) or desired_n <= 0:
            raise ValueError("desired_n must be a positive finite number")

        self.model = ReactorModel()
        self.duration = float(duration)
        self.dt = float(dt)
        self.desired_n = float(desired_n)

        self.safety = None  # SafetySupervisor from the most recent run
        self._clear_history()

    def _clear_history(self):
        """Clear traces so a repeated run does not append to old data."""

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
        self.control_durations = []
        self.control_values = []            # rho actually applied to the reactor
        self.commanded_rho_values = []      # rho the controller asked for
        self.safety_states = []

    def _build_safety_supervisor(self):
        """Build the safety limits used for each run."""

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
        """Build an EKF for power, six precursors, and three temperatures."""

        n_states = current_state.shape[0]

        # Sensors measure power (state 0) and temperatures (states 7, 8, 9).
        H = np.zeros((4, n_states))
        H[0, 0] = 1.0
        H[1, 7] = 1.0
        H[2, 8] = 1.0
        H[3, 9] = 1.0

        # Measurement covariance comes from each sensor's configured noise.
        R = np.diag([
            sensor_suite.power.sigma ** 2,
            sensor_suite.fuel_temp.sigma ** 2,
            sensor_suite.coolant_temp_1.sigma ** 2,
            sensor_suite.coolant_temp_2.sigma ** 2,
        ])

        # Precursor values span several orders of magnitude, so their process
        # noise is scaled to their steady-state size. This also lets the EKF
        # absorb disturbances that are deliberately absent from its model.
        q_power = 1e-5
        q_precursor_relative = 1e-2
        q_temp = 1e-2

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
        """Apply a stuck or delayed control-rod fault.

        ``actuator_fault`` is ``None`` or one of:
          {"type": "stuck", "t_start": <s>, "value": <optional fixed rho>}
          {"type": "delay", "t_start": <s>, "lag_steps": <int>}
        """

        if actuator_fault is None or t < actuator_fault.get("t_start", 0.0):
            return commanded_rho

        fault_type = actuator_fault.get("type")
        if fault_type == "stuck":
            if "value" in actuator_fault:
                return actuator_fault["value"]
            return applied_history[-1] if applied_history else 0.0

        if fault_type == "delay":
            lag = actuator_fault.get("lag_steps", 10)
            if not isinstance(lag, int) or isinstance(lag, bool) or lag < 1:
                raise ValueError("lag_steps must be a positive integer")
            if len(commanded_history) < lag:
                return 0.0
            return commanded_history[-lag]

        raise ValueError(f"Unsupported actuator fault: {fault_type!r}")

    def _read_and_update_estimate(self, state, sensor_suite, ekf):
        """Read all sensors and update the EKF with finite channels."""

        readings = sensor_suite.read_all(state, self.model.rho_rod)
        measurements = np.array([readings[name] for name in CHANNELS])
        healthy = np.isfinite(measurements)

        # Keep working sensors in service when another channel drops out.
        if healthy.all():
            ekf.update(measurements)
        elif healthy.any():
            ekf.update(
                measurements[healthy],
                H=ekf.H[healthy],
                R=ekf.R[np.ix_(healthy, healthy)],
            )

        return readings

    def simulate(self, controller, sensor_suite, use_filter=True, actuator_fault=None):
        """Run the closed loop and return the final reactor state."""

        current_state = self.model.x0.copy()
        number_of_steps = math.ceil(self.duration / self.dt)

        # Reset plant inputs in case this Simulation has already been run.
        rod_position = 0.0
        self.model.rho_rod = 0.0
        ordered_rho = []

        ekf = self._build_ekf(current_state, sensor_suite)
        self.safety = self._build_safety_supervisor()

        self._clear_history()
        readings = self._read_and_update_estimate(current_state, sensor_suite, ekf)
        self._record_state(
            0.0,
            current_state,
            measured_n=readings["power"],
            estimated_n=ekf.x[0],
        )

        for i in range(number_of_steps):
            t = i * self.dt
            remaining = self.duration - t
            if remaining <= 0:
                break
            step_dt = min(self.dt, remaining)

            current_n = ekf.x[0] if use_filter else readings["power"]

            raw_speed = controller.update(self.desired_n, current_n, step_dt)
            try:
                speed = float(raw_speed)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "controller must return one numeric rod speed"
                ) from exc
            if not np.isfinite(speed):
                raise ValueError("controller returned a non-finite rod speed")
            speed = float(np.clip(speed, -MAX_ROD_SPEED, MAX_ROD_SPEED))
            rod_position = float(np.clip(
                rod_position + speed * step_dt,
                ROD_MIN,
                ROD_MAX,
            ))
            commanded_rho = rod_position

            safety_state = self.safety.evaluate({
                "power": readings["power"],
                "fuel_temp": readings["fuel_temp"],
                "coolant_temp": 0.5 * (
                    readings["coolant_1_temp"]
                    + readings["coolant_2_temp"]
                ),
            })
            supervised_rho = float(self.safety.apply(commanded_rho))

            if self.safety.state in ("SCRAM", "SHUTDOWN"):
                # SCRAM uses separate shutdown rods, so a control-rod drive
                # fault cannot prevent the emergency insertion.
                actual_rho = supervised_rho
            else:
                rod_position = supervised_rho
                actual_rho = self._apply_actuator_fault(
                    supervised_rho,
                    ordered_rho,
                    self.control_values,
                    t,
                    actuator_fault,
                )

            if not np.isfinite(actual_rho):
                raise ValueError("actuator produced non-finite reactivity")
            actual_rho = float(actual_rho)
            ordered_rho.append(supervised_rho)

            self.control_times.append(t)
            self.control_durations.append(step_dt)
            self.commanded_rho_values.append(commanded_rho)
            self.safety_states.append(safety_state)
            self.control_values.append(actual_rho)

            self.model.rho_rod = actual_rho
            solution = solve_ivp(
                fun=self.model.dynamics,
                t_span=(t, t + step_dt),
                y0=current_state,
                t_eval=[t + step_dt],
                method="Radau",
            )
            if not solution.success:
                raise RuntimeError(solution.message)

            current_state = solution.y[:, -1]

            ekf.predict(actual_rho, dt=step_dt)
            sensor_suite.step(step_dt)
            readings = self._read_and_update_estimate(
                current_state, sensor_suite, ekf
            )

            self._record_state(
                t + step_dt,
                current_state,
                measured_n=readings["power"],
                estimated_n=ekf.x[0],
            )

        return current_state

    def _record_state(self, t, state, measured_n, estimated_n):
        """Append one sample to each state history."""

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
