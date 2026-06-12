import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


class ReactorModel:
    # Fraction of neutrons that are delayed
    BETA_I = np.array([0.000215, 0.001424,
                       0.001274, 0.002568,
                       0.000748, 0.000273])

    # Precursor decay constants, units 1/s
    LAMBDA_I = np.array([0.0124, 0.0305, 0.111,
                         0.301, 1.14, 3.01])

    # Total delayed neutron fraction
    BETA = BETA_I.sum()

    # Prompt neutron generation time, seconds
    LAMBDA = 5e-5

    P_rated    = 100e6        # 100 MW thermal power [W]

    # Heat capacities
    mCp_fuel   = 4.0e6        # fuel thermal mass [J/K]
    mCp_cool   = 1.0e6        # coolant thermal mass per node [J/K]

    # Time constants
    tau_fuel   = 6.0          # fuel-to-coolant transfer [s]
    tau_cool   = 3.0          # coolant heat transfer [s]
    tau_flow   = 4.0          # coolant transit time [s]

    # Reference temperature
    T_inlet     = 560.0       # [K]

    # Reactivity feedback coefficients
    alpha_fuel    = -2.5e-5   # [dk/k per K]
    alpha_cool    = -8.0e-5   # [dk/k per K]

    def __init__(self):
        # Initial steady state values
        self.n0 = 1.0

        self.C0 = (self.BETA_I / (self.LAMBDA * self.LAMBDA_I)) * self.n0

        self.T_fuel0, self.T_c1_0, self.T_c2_0 = self.calculate_steady_state_temps()

        self.T_fref = self.T_fuel0
        self.T_cref = (self.T_c1_0 + self.T_c2_0) / 2
        

        # x = [n, C1, C2, C3, C4, C5, C6, T_fuel, T_c1, T_c2]

        self.x0 = np.concatenate(([self.n0], self.C0, self.T_fuel0, self.T_c1_0, self.T_c2_0))


    def rho_external(self, t):
        #from the rod
        return 0.0001 if t >= 10 else 0.0
    
    def rho_feedback(self, t):
        #reactivity feedback from temperature changes
        return self.alpha_f*(self.x0[7] - self.T_fref) + self.alpha_c*(self.x0[8] - self.T_cref))

    def rho_total(self, t):
        # Total reactivity is sum of external and feedback
        return self.rho_external(t) + self.rho_feedback(t)
    
    def calculate_steady_state_temps(self):
        #Set dT/dt = 0 and solve for T_fuel, T_c1, T_c2
        

    def neutron_equations(self, t, x):
        # Neutron population, corresponds to reactor power
        n = x[0]

        # Precursor concentrations
        C = x[1:7]

        rho = self.rho_func(t)

        dndt = ((rho - self.BETA) / self.LAMBDA) * n + np.dot(self.LAMBDA_I, C)

        dCdt = (self.BETA_I / self.LAMBDA) * n - self.LAMBDA_I * C

        return np.concatenate(([dndt], dCdt))
    
    def thermal_equations():
        #Mann's thermal model for point reactor

        

    def solve(self):
        sol = solve_ivp(
            fun=self.point_kinetics,
            t_span=(0, 200),
            y0=self.x0,
            method="RK45",
            max_step=0.1,
            dense_output=True
        )

        return sol
    
model=ReactorModel()
sol = model.solve()

t = sol.t        # time values from solve_ivp
n = sol.y[0]     # neutron population over time

plt.figure(figsize=(10, 4))
plt.plot(t, n)
plt.xlabel('Time (s)')
plt.ylabel('Neutron density (normalized)')
plt.title('Point Kinetics — Step Reactivity Response')
plt.grid(True)
plt.show()

