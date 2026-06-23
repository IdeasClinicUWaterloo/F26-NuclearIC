import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

from control import Controller


class ReactorModel:
    # Fraction of neutrons that are delayed
    BETA_I = np.array([0.000215, 0.001424, 0.001274, 0.002568, 0.000748, 0.000273])

    # Precursor decay constants [1/s]
    LAMBDA_I = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])

    # Total delayed neutron fraction and average decay constant
    BETA = BETA_I.sum()
    LAMBDA = 5e-5


    P_rated = 100e6 # Power rating of the reactor in Watts
    mCp_fuel = 4.0e6 # Heat capacity of the fuel in J/K
    mCp_cool = 1.0e6 # Heat capacity of the coolant in J/K

    tau_fuel = 6.0 # Time constant for heat transfer from fuel to coolant in seconds
    tau_cool = 3.0 # Time constant for heat transfer within the coolant in seconds
    tau_flow = 4.0 # Time constant for coolant flow in seconds

    T_inlet = 560.0 # Inlet temperature of the coolant in Kelvin
    alpha_fuel = -2.5e-5 # Fuel temperature coefficient
    alpha_cool = -8.0e-5 # Coolant temperature coefficient

    def __init__(self):
        self.n0 = 1.0
        self.rho_rod = 0.0
        self.C0 = (self.BETA_I / (self.LAMBDA * self.LAMBDA_I)) * self.n0

        self.T_fuel0, self.T_c1_0, self.T_c2_0 = self.calculate_steady_state_temps()
        self.T_fref = self.T_fuel0
        self.T_cref = 0.5 * (self.T_c1_0 + self.T_c2_0)

        # x = [n, C1, C2, C3, C4, C5, C6, T_fuel, T_c1, T_c2]
        self.x0 = np.concatenate(
            ([self.n0], self.C0, [self.T_fuel0, self.T_c1_0, self.T_c2_0])
        )

    def calculate_steady_state_temps(self):
        P0 = self.P_rated * self.n0
        fuel_to_coolant_delta = P0 * self.tau_fuel / self.mCp_fuel

        T_c1_0 = self.T_inlet + (self.tau_flow / self.tau_cool) * fuel_to_coolant_delta
        T_c2_0 = T_c1_0
        T_fuel0 = T_c1_0 + fuel_to_coolant_delta
        return T_fuel0, T_c1_0, T_c2_0

    def rho_external(self, t):
        """Control-rod reactivity held constant during one simulation timestep."""
        return self.rho_rod

    def rho_disturbance(self, t):
        """Optional uncommanded reactivity insertion; zero for the baseline case."""
        return 0.001 if 50 <= t < 60 else 0.0

    def rho_feedback(self, T_fuel, T_c_avg):
        return (
            self.alpha_fuel * (T_fuel - self.T_fref)
            + self.alpha_cool * (T_c_avg - self.T_cref)
        )

    def rho_total(self, t, T_fuel, T_c_avg):
        return (
            self.rho_external(t)
            + self.rho_disturbance(t)
            + self.rho_feedback(T_fuel, T_c_avg)
        )

    def neutron_equations(self, n, C, rho):
        dndt = ((rho - self.BETA) / self.LAMBDA) * n + np.dot(self.LAMBDA_I, C)
        dCdt = (self.BETA_I / self.LAMBDA) * n - self.LAMBDA_I * C
        return dndt, dCdt

    def thermal_equations(self, n, T_fuel, T_c1, T_c2):
        P = self.P_rated * n
        T_c_avg = 0.5 * (T_c1 + T_c2)

        dT_fuel_dt = P / self.mCp_fuel - (T_fuel - T_c_avg) / self.tau_fuel
        dT_c1_dt = (
            (T_fuel - T_c1) / self.tau_cool
            - (T_c1 - self.T_inlet) / self.tau_flow
        )
        dT_c2_dt = (T_c1 - T_c2) / self.tau_cool
        return np.array([dT_fuel_dt, dT_c1_dt, dT_c2_dt])

    def dynamics(self, t, x):
        n = x[0]
        C = x[1:7]
        T_fuel, T_c1, T_c2 = x[7:10]
        T_c_avg = 0.5 * (T_c1 + T_c2)

        rho = self.rho_total(t, T_fuel, T_c_avg)
        dndt, dCdt = self.neutron_equations(n, C, rho)
        dTdt = self.thermal_equations(n, T_fuel, T_c1, T_c2)
        return np.concatenate(([dndt], dCdt, dTdt))


class Simulation:
    def __init__(self, duration=200.0, dt=0.1, desired_n=1.0):
        self.model = ReactorModel()
        self.duration = duration
        self.dt = dt
        self.desired_n = desired_n

        self.time_steps = []
        self.control_times = []
        self.control_values = []
        self.n_current_values = []
        self.n_desired_values = []

    def simulate(self, controller):
        current_state = self.model.x0.copy()
        number_of_steps = int(self.duration / self.dt)

        self.time_steps = [0.0]
        self.n_current_values = [current_state[0]]
        self.n_desired_values = [self.desired_n]
        self.control_times = []
        self.control_values = []

        for i in range(number_of_steps):
            t = i * self.dt
            current_n = current_state[0]

            self.model.rho_rod = controller.update(self.desired_n, current_n, self.dt)
            self.control_times.append(t)
            self.control_values.append(self.model.rho_rod)

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
            self.time_steps.append(t + self.dt)
            self.n_current_values.append(current_state[0])
            self.n_desired_values.append(self.desired_n)

        return current_state

    def plot(self):
        plt.figure(figsize=(12, 6))

        plt.subplot(2, 1, 1)
        plt.plot(self.time_steps, self.n_current_values, label="Current neutron population")
        plt.plot(
            self.time_steps,
            self.n_desired_values,
            "--",
            label="Desired neutron population",
        )
        plt.xlabel("Time (s)")
        plt.ylabel("Normalized power")
        plt.title("Closed-Loop Reactor Power")
        plt.legend()
        plt.grid()

        plt.subplot(2, 1, 2)
        plt.plot(
            self.control_times,
            self.control_values,
            label="Control-rod reactivity",
            color="orange",
        )
        plt.xlabel("Time (s)")
        plt.ylabel("Reactivity, rho (dk/k)")
        plt.title("PID Control-Rod Command")
        plt.legend()
        plt.grid()

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    controller = Controller(kp=1e-4, ki=1e-5, kd=1e-5)
    simulator = Simulation(duration=200.0, dt=0.1, desired_n=1.0)
    final_state = simulator.simulate(controller)

    print("Initial temperatures:")
    print(f"T_fuel0 = {simulator.model.T_fuel0:.2f} K")
    print(f"T_c1_0  = {simulator.model.T_c1_0:.2f} K")
    print(f"T_c2_0  = {simulator.model.T_c2_0:.2f} K")
    print(f"T_cref  = {simulator.model.T_cref:.2f} K")
    print(f"Final normalized power = {final_state[0]:.6f}")

    simulator.plot()
