"""Point-kinetics and lumped thermal model used by the simulation and EKF."""

import numpy as np
from scipy.integrate import solve_ivp


class ReactorModel:
    # Delayed-neutron fractions for the six precursor groups.
    BETA_I = np.array([0.000215, 0.001424, 0.001274, 0.002568, 0.000748, 0.000273])

    # Precursor decay constants [1/s].
    LAMBDA_I = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])

    # Total delayed-neutron fraction and prompt-neutron generation time [s].
    BETA = BETA_I.sum()
    GENERATION_TIME = 5e-5

    P_rated = 100e6  # Rated thermal power [W].
    mCp_fuel = 4.0e6  # Lumped fuel heat capacity [J/K].

    tau_fuel = 6.0  # Fuel-to-coolant heat-transfer time [s].
    tau_cool = 3.0  # Coolant-node heat-transfer time [s].
    tau_flow = 4.0  # Coolant residence time [s].

    T_inlet = 560.0  # Coolant inlet temperature [K].
    alpha_fuel = -2.5e-5  # Fuel temperature coefficient [reactivity/K].
    alpha_cool = -8.0e-5  # Coolant temperature coefficient [reactivity/K].

    def __init__(self, disturbance_start=50.0, disturbance_end=100.0,
                 disturbance_magnitude=0.0001):
        self.n0 = 1.0
        self.rho_rod = 0.0
        self.C0 = (
            self.BETA_I / (self.GENERATION_TIME * self.LAMBDA_I)
        ) * self.n0

        self.disturbance_start = disturbance_start
        self.disturbance_end = disturbance_end
        self.disturbance_magnitude = disturbance_magnitude

        self.T_fuel0, self.T_c1_0, self.T_c2_0 = (
            self.calculate_steady_state_temps()
        )
        self.T_fref = self.T_fuel0
        self.T_cref = 0.5 * (self.T_c1_0 + self.T_c2_0)

        # x = [n, C1, C2, C3, C4, C5, C6, T_fuel, T_c1, T_c2]
        self.x0 = np.concatenate(
            ([self.n0], self.C0, [self.T_fuel0, self.T_c1_0, self.T_c2_0])
        )

    def calculate_steady_state_temps(self):
        """Return fuel and coolant temperatures at rated steady state."""

        P0 = self.P_rated * self.n0
        fuel_to_coolant_delta = P0 * self.tau_fuel / self.mCp_fuel

        T_c1_0 = (
            self.T_inlet
            + (self.tau_flow / self.tau_cool) * fuel_to_coolant_delta
        )
        T_c2_0 = T_c1_0
        T_fuel0 = T_c1_0 + fuel_to_coolant_delta
        return T_fuel0, T_c1_0, T_c2_0

    def rho_external(self, _t):
        """Return the control-rod reactivity held during this solver step."""

        return self.rho_rod

    def rho_disturbance(self, t):
        """Return the configured reactivity disturbance at time ``t``."""

        if self.disturbance_start <= t < self.disturbance_end:
            return self.disturbance_magnitude
        return 0.0

    def rho_feedback(self, T_fuel, T_c_avg):
        """Return the negative reactivity feedback from temperature changes."""

        return (
            self.alpha_fuel * (T_fuel - self.T_fref)
            + self.alpha_cool * (T_c_avg - self.T_cref)
        )

    def rho_total(self, t, T_fuel, T_c_avg):
        """Return control, disturbance, and thermal reactivity combined."""

        return (
            self.rho_external(t)
            + self.rho_disturbance(t)
            + self.rho_feedback(T_fuel, T_c_avg)
        )

    def neutron_equations(self, n, C, rho):
        """Return point-kinetics rates for power and precursor groups."""

        dndt = (
            ((rho - self.BETA) / self.GENERATION_TIME) * n
            + np.dot(self.LAMBDA_I, C)
        )
        dCdt = (
            (self.BETA_I / self.GENERATION_TIME) * n
            - self.LAMBDA_I * C
        )
        return dndt, dCdt

    def thermal_equations(self, n, T_fuel, T_c1, T_c2):
        """Return temperature rates for the fuel and two coolant nodes."""

        power = self.P_rated * n
        T_c_avg = 0.5 * (T_c1 + T_c2)

        dT_fuel_dt = power / self.mCp_fuel - (T_fuel - T_c_avg) / self.tau_fuel
        dT_c1_dt = (
            (T_fuel - T_c1) / self.tau_cool
            - (T_c1 - self.T_inlet) / self.tau_flow
        )
        dT_c2_dt = (T_c1 - T_c2) / self.tau_cool
        return np.array([dT_fuel_dt, dT_c1_dt, dT_c2_dt])

    def dynamics(self, t, x):
        """Return the complete state derivative for the plant model."""

        n = x[0]
        C = x[1:7]
        T_fuel, T_c1, T_c2 = x[7:10]
        T_c_avg = 0.5 * (T_c1 + T_c2)

        rho = self.rho_total(t, T_fuel, T_c_avg)
        dndt, dCdt = self.neutron_equations(n, C, rho)
        dTdt = self.thermal_equations(n, T_fuel, T_c1, T_c2)
        return np.concatenate(([dndt], dCdt, dTdt))

    def filter_dynamics(self, x, rho_rod):
        """Return EKF dynamics without the unmeasured external disturbance."""

        n = x[0]
        C = x[1:7]
        T_fuel, T_c1, T_c2 = x[7:10]
        T_c_avg = 0.5 * (T_c1 + T_c2)

        rho = rho_rod + self.rho_feedback(T_fuel, T_c_avg)
        dndt, dCdt = self.neutron_equations(n, C, rho)
        dTdt = self.thermal_equations(n, T_fuel, T_c1, T_c2)

        return np.concatenate(([dndt], dCdt, dTdt))

    def propagate(self, x, rho_rod, dt):
        """Propagate an EKF state by ``dt`` at fixed rod reactivity."""

        solution = solve_ivp(
            fun=lambda t, xx: self.filter_dynamics(xx, rho_rod),
            t_span=(0.0, dt),
            y0=x,
            method="Radau",
        )

        if not solution.success:
            raise RuntimeError(solution.message)

        return solution.y[:, -1]
