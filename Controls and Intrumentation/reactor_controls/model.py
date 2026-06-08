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

    def __init__(self):
        # Initial steady state values
        self.n0 = 1.0

        self.C0 = (self.BETA_I / (self.LAMBDA * self.LAMBDA_I)) * self.n0

        # x = [n, C1, C2, C3, C4, C5, C6]
        self.x0 = np.concatenate(([self.n0], self.C0))

    def rho_func(self, t):
        return 0.0001 if t >= 10 else 0.0

    def point_kinetics(self, t, x):
        # Neutron population, corresponds to reactor power
        n = x[0]

        # Precursor concentrations
        C = x[1:]

        rho = self.rho_func(t)

        dndt = ((rho - self.BETA) / self.LAMBDA) * n + np.dot(self.LAMBDA_I, C)

        dCdt = (self.BETA_I / self.LAMBDA) * n - self.LAMBDA_I * C

        return np.concatenate(([dndt], dCdt))

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

