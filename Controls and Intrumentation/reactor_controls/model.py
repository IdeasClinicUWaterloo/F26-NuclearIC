import numpy as np
from scipy.integrate import solve_ivp
from control import Controller
import matplotlib.pyplot as plt


class ReactorModel:
    # Fraction of neutrons that are delayed
    BETA_I = np.array([0.000215, 0.001424,
                       0.001274, 0.002568,
                       0.000748, 0.000273])

    # Precursor decay constants [1/s]
    LAMBDA_I = np.array([0.0124, 0.0305, 0.111,
                         0.301, 1.14, 3.01])

    # Total delayed neutron fraction
    BETA = BETA_I.sum()

    # Prompt neutron generation time [s]
    LAMBDA = 5e-5

    # Rated power [W]
    P_rated    = 100e6        # 100 MW thermal power [W]

    # Heat capacities
    mCp_fuel   = 4.0e6        # fuel thermal mass [J/K]
    mCp_cool   = 1.0e6        # coolant thermal mass per node [J/K]

    # Time constants
    tau_fuel   = 6.0          # fuel-to-coolant transfer [s]
    tau_cool   = 3.0          # coolant heat transfer [s]
    tau_flow   = 4.0          # coolant transit time [s]

    # Inlet coolant temperature [K]
    T_inlet = 560.0

    # Reactivity feedback coefficients [dk/k per K]
    alpha_fuel = -2.5e-5
    alpha_cool = -8.0e-5

    def __init__(self):
        self.n0 = 1.0

        # Initial precursor concentrations from steady-state point kinetics
        self.C0 = (self.BETA_I / (self.LAMBDA * self.LAMBDA_I)) * self.n0

        # Initial steady-state temperatures
        self.T_fuel0, self.T_c1_0, self.T_c2_0 = self.calculate_steady_state_temps()

        # Reference temperatures for feedback
        self.T_fref = self.T_fuel0
        self.T_cref = 0.5 * (self.T_c1_0 + self.T_c2_0)

        # x = [n, C1, C2, C3, C4, C5, C6, T_fuel, T_c1, T_c2]
        self.x0 = np.concatenate((
            [self.n0],
            self.C0,
            [self.T_fuel0, self.T_c1_0, self.T_c2_0]
        ))

        self.rho_rod = 0.0  # Control rod reactivity, to be updated by the controller

    def calculate_steady_state_temps(self):
        P0 = self.P_rated * self.n0

        # From fuel steady state:
        # T_fuel - T_c_avg = P0 * tau_fuel / mCp_fuel
        fuel_to_coolant_delta = P0 * self.tau_fuel / self.mCp_fuel

        # From coolant node 2 steady state:
        # T_c1 = T_c2
        T_c1_0 = self.T_inlet + (
            self.tau_flow / self.tau_cool
        ) * fuel_to_coolant_delta

        T_c2_0 = T_c1_0

        T_fuel0 = T_c1_0 + fuel_to_coolant_delta

        return T_fuel0, T_c1_0, T_c2_0
    
    def rho_feedback(self, T_fuel, T_c_avg):
        #reactivity feedback from temperature changes
        return (
            self.alpha_fuel * (T_fuel - self.T_fref)
            + self.alpha_cool * (T_c_avg - self.T_cref)
        )

    def rho_total(self, t, T_fuel, T_c_avg):
        # Total reactivity is sum of external and feedback
        return self.rho_rod + self.rho_feedback(T_fuel, T_c_avg)

    def neutron_equations(self, n, C, rho):

        dndt = ((rho - self.BETA) / self.LAMBDA) * n + np.dot(self.LAMBDA_I, C)
        dCdt = (self.BETA_I / self.LAMBDA) * n - self.LAMBDA_I * C

        return dndt, dCdt
    
    def thermal_equations(self, n, T_fuel, T_c1, T_c2):

        # Mann's thermal model for point reactor
        P = self.P_rated * n
        T_c_avg = 0.5 * (T_c1 + T_c2)

        dT_fuel_dt = (
            P / self.mCp_fuel
            - (T_fuel - T_c_avg) / self.tau_fuel
        )

        dT_c1_dt = (
            (T_fuel - T_c1) / self.tau_cool
            - (T_c1 - self.T_inlet) / self.tau_flow
        )

        dT_c2_dt = (
            (T_c1 - T_c2) / self.tau_cool
        )

        return np.array([dT_fuel_dt, dT_c1_dt, dT_c2_dt])

    def dynamics(self, t, x):
        # Neutron population, corresponds to reactor power
        n = x[0]

        # Precursor concentrations
        C = x[1:7]

        # Thermal temperatures
        T_fuel = x[7]
        T_c1 = x[8]
        T_c2 = x[9]
        T_c_avg = 0.5 * (T_c1 + T_c2)

        rho = self.rho_total(t, T_fuel, T_c_avg)

        dndt, dCdt = self.neutron_equations(n, C, rho)
        dTdt = self.thermal_equations(n, T_fuel, T_c1, T_c2)

        return np.concatenate(([dndt], dCdt, dTdt))

class Simulation:
    def __init__(self):
        self.model = ReactorModel()
        self.dt = 0.1  # Time step for simulation
        self.desired_n = 1.0  # Desired neutron population
        self.current_n = 0

        self.time_steps = []
        self.control_values = []
        self.n_current_values = []
        self.n_desired_values = []

    #Solve the model, discretely sample the solution, and return the time and state arrays

    def simulate(self, controller):
        for i in range(200):
            t = i * self.dt
            self.time_steps.append(t)

            # Get current neutron population from the model
            self.current_n = self.model.x0[0]

            # Update the control rod reactivity using the PID controller
            rho_rod = controller.update(self.desired_n, self.current_n, self.dt)
            self.control_values.append(rho_rod)

            # Define the external reactivity function for the model
            self.model.rho_external = rho_rod

            # Solve the model for the next time step
            sol = solve_ivp(
                fun=self.model.dynamics,
                t_span=(t, t + self.dt),
                y0=self.model.x0,
                method='RK45'
            )

            # Update the model's state for the next iteration
            self.model.x0 = sol.y[:, -1]
            self.n_current_values.append(self.n_current)
            self.n_desired_values.append(self.n_desired)

    def plot(self):
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(self.time_steps, self.n_current_values, label='Current Neutron Population')
        plt.plot(self.time_steps, self.n_desired_values, label='Desired Neutron Population', linestyle='--')
        plt.xlabel('Time (s)')
        plt.ylabel('Neutron Population')
        plt.title('Neutron Population Over Time')
        plt.legend()
        plt.grid()

        plt.subplot(2, 1, 2)
        plt.plot(self.time_steps, self.control_values, label='Control Rod Reactivity (rho_rod)', color='orange')
        plt.xlabel('Time (s)')
        plt.ylabel('Control Rod Reactivity')
        plt.title('Control Rod Reactivity Over Time')
        plt.legend()
        plt.grid()

        plt.tight_layout()
        plt.show()
    
simulator = Simulation()
sol = simulator.simulate(Controller(kp=0.5, ki=0.1, kd=0.05))
simulator.plot()
