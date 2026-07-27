import numpy as np
from scipy.linalg import expm


class EKF:
    def __init__(self, model, H, Q, R, x0, P0, dt, jac_eps=1e-6):

        self.model = model
        self.propagate = self.model.propagate

        self.H = H  # Observation matrix
        self.Q = Q  # Process noise cov.
        self.R = R  # Sensor noise cov.
        self.x = x0  # State estimate
        self.P = P0  # Covariance (uncertainty in x)
        self.dt = dt  # Timestep, used to discretize the Jacobian
        self.jac_eps = jac_eps  # Nudge size for the numerical Jacobian

        # Innovation (measurement residual) and its covariance from the
        # most recent update() -- exposed so a fault monitor can watch
        # "how surprised was the filter by this measurement" per channel.
        self.last_y = None
        self.last_S = None

    def _numerical_jacobian(self, rho_rod):
        """Estimates d(filter_dynamics)/dx at the current state by nudging
        each state entry up and down and seeing how much the dynamics
        respond."""

        n = len(self.x)
        A = np.zeros((n, n))

        for j in range(n):
            dx = np.zeros(n)
            dx[j] = self.jac_eps

            rhs_plus = self.model.filter_dynamics(self.x + dx, rho_rod)
            rhs_minus = self.model.filter_dynamics(self.x - dx, rho_rod)

            A[:, j] = (rhs_plus - rhs_minus) / (2 * self.jac_eps)

        return A

    def predict(self, rho_rod):
        """Predicts the next state estimate and covariance, linearizing the
        nonlinear dynamics about the current estimate to propagate P."""

        A = self._numerical_jacobian(rho_rod)
        # Matrix exponential, not I + A*dt: the reactor's neutron mode is
        # stiff (~-130 /s), so a first-order Euler discretization of the
        # Jacobian is unstable at this dt. expm handles fast-decaying modes
        # correctly instead of blowing them up.
        F = expm(A * self.dt)

        self.x = self.propagate(self.x, rho_rod, self.dt)
        self.P = F @ self.P @ F.T + self.Q

        return self.x

    def update(self, z):
        """Updates the state estimate and covariance based on measurement z.
        Identical to a linear KalmanFilter's update, since the measurement
        model here (sensors reading state entries directly) is linear."""

        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = self.P - K @ self.H @ self.P

        self.last_y = y
        self.last_S = S

        return self.x

    def normalized_innovation(self):
        """Returns |innovation| / sigma per measurement channel from the
        most recent update() -- how many standard deviations away each
        sensor reading was from what the filter expected. A channel that's
        consistently large here (not just occasionally, which noise alone
        will do) suggests that sensor, not the model, is wrong."""

        if self.last_y is None:
            return None

        sigma = np.sqrt(np.diag(self.last_S))
        return np.abs(self.last_y) / sigma
