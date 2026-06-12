import numpy as np
from scipy.integrate import solve_ivp
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

    def calculate_steady_state_temps(self):
        """
        Compute steady-state temperatures bottom-up.

        This version makes the thermal equations consistent with the initial state.
        """
        P0 = self.P_rated * self.n0

        # At steady state, the fuel transfers P0 to the coolant.
        # Split heat equally into the two coolant nodes.
        heat_to_each_coolant_node = 0.5 * P0

        # Coolant node 1 receives inlet flow.
        T_c1_0 = self.T_inlet + heat_to_each_coolant_node * self.tau_flow / self.mCp_cool

        # Coolant node 2 receives flow from coolant node 1.
        T_c2_0 = T_c1_0 + heat_to_each_coolant_node * self.tau_flow / self.mCp_cool

        T_c_avg = 0.5 * (T_c1_0 + T_c2_0)

        # From dT_fuel/dt = 0:
        # 0 = P0/mCp_fuel - (T_fuel - T_c_avg)/tau_fuel
        T_fuel0 = T_c_avg + (P0 * self.tau_fuel) / self.mCp_fuel

        return T_fuel0, T_c1_0, T_c2_0
    
    def rho_external(self, t):
        #from the rod
        return 0.001 if t >= 10 else 0.0
    
    def rho_feedback(self, T_fuel, T_c_avg):
        #reactivity feedback from temperature changes
        return (
            self.alpha_fuel * (T_fuel - self.T_fref)
            + self.alpha_cool * (T_c_avg - self.T_cref)
        )

    def rho_total(self, t, T_fuel, T_c_avg):
        # Total reactivity is sum of external and feedback
        return self.rho_external(t) + self.rho_feedback(T_fuel, T_c_avg)

    def neutron_equations(self, n, C, rho):

        dndt = ((rho - self.BETA) / self.LAMBDA) * n + np.dot(self.LAMBDA_I, C)
        dCdt = (self.BETA_I / self.LAMBDA) * n - self.LAMBDA_I * C

        return dndt, dCdt
    
    def thermal_equations(self, n, T_fuel, T_c1, T_c2):

        # Mann's thermal model for point reactor
        P = self.P_rated * n
        T_c_avg = 0.5 * (T_c1 + T_c2)

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

    def solve(self):
        sol = solve_ivp(
            fun=self.dynamics,
            t_span=(0, 200),
            y0=self.x0,
            method="RK45",
            max_step=0.1,
            dense_output=True
        )

        return sol
    
model=ReactorModel()
sol = model.solve()

print("Initial temperatures:")
print(f"T_fuel0 = {model.T_fuel0:.2f} K")
print(f"T_c1_0  = {model.T_c1_0:.2f} K")
print(f"T_c2_0  = {model.T_c2_0:.2f} K")
print(f"T_cref  = {model.T_cref:.2f} K")

t = sol.t        # time values from solve_ivp
n = sol.y[0]     # neutron population over time

plt.figure(figsize=(10, 4))
plt.plot(t, n)
plt.xlabel('Time (s)')
plt.ylabel('Neutron density (normalized)')
plt.title('Point Kinetics: Reactivity Response')
plt.grid(True)
plt.show()
