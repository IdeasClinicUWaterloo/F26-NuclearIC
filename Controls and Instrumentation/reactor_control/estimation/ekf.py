"""Extended Kalman filter for the ten-state reactor model.

Each cycle predicts the state with the reactor model, then corrects that
prediction with the available power and temperature readings. ``Q`` describes
model uncertainty; ``R`` describes measurement uncertainty.
"""

import numpy as np
from scipy.linalg import expm


class EKF:
    def __init__(self, model, H, Q, R, x0, P0, dt, jac_eps=1e-6):
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be a positive finite number")
        if not np.isfinite(jac_eps) or jac_eps <= 0:
            raise ValueError("jac_eps must be a positive finite number")

        self.model = model
        self.H = np.array(H, dtype=float, copy=True)
        self.Q = np.array(Q, dtype=float, copy=True)
        self.R = np.array(R, dtype=float, copy=True)
        self.x = np.array(x0, dtype=float, copy=True)
        self.P = np.array(P0, dtype=float, copy=True)
        self.dt = float(dt)
        self.jac_eps = float(jac_eps)

        # Retain the latest residual and covariance for diagnostics.
        self.last_y = None
        self.last_S = None

    def _numerical_jacobian(self, rho_rod):
        """Linearize the reactor dynamics around the current estimate."""

        n_states = len(self.x)
        jacobian = np.zeros((n_states, n_states))

        for column in range(n_states):
            offset = np.zeros(n_states)
            offset[column] = self.jac_eps

            rhs_plus = self.model.filter_dynamics(self.x + offset, rho_rod)
            rhs_minus = self.model.filter_dynamics(self.x - offset, rho_rod)
            jacobian[:, column] = (
                (rhs_plus - rhs_minus) / (2 * self.jac_eps)
            )

        return jacobian

    def predict(self, rho_rod, dt=None):
        """Advance the state and covariance by one timestep."""

        step_dt = self.dt if dt is None else dt
        if not np.isfinite(step_dt) or step_dt <= 0:
            raise ValueError("dt must be a positive finite number")

        jacobian = self._numerical_jacobian(rho_rod)

        # The prompt-neutron mode is too fast for the usual I + A*dt shortcut.
        transition = expm(jacobian * step_dt)

        self.x = self.model.propagate(self.x, rho_rod, step_dt)
        process_noise = self.Q * (step_dt / self.dt)
        self.P = transition @ self.P @ transition.T + process_noise
        self.P = 0.5 * (self.P + self.P.T)

        return self.x

    def update(self, z, H=None, R=None):
        """Correct the estimate with the supplied measurement channels.

        Pass reduced ``H`` and ``R`` matrices when only some sensors are
        available.
        """

        H = self.H if H is None else np.asarray(H, dtype=float)
        R = self.R if R is None else np.asarray(R, dtype=float)
        z = np.asarray(z, dtype=float)

        innovation = z - H @ self.x
        innovation_covariance = H @ self.P @ H.T + R

        # Solving the linear system is more stable than forming S^-1 directly.
        kalman_gain = np.linalg.solve(
            innovation_covariance, H @ self.P
        ).T

        self.x = self.x + kalman_gain @ innovation

        # Joseph form preserves symmetry and positive semi-definiteness better
        # than the shorter P - KHP update.
        identity = np.eye(len(self.x))
        correction = identity - kalman_gain @ H
        self.P = (
            correction @ self.P @ correction.T
            + kalman_gain @ R @ kalman_gain.T
        )
        self.P = 0.5 * (self.P + self.P.T)

        self.last_y = innovation
        self.last_S = innovation_covariance

        return self.x

    def normalized_innovation(self):
        """Return each residual divided by its expected standard deviation.

        Large values flag disagreement with the model, but they do not by
        themselves identify which sensor is faulty.
        """

        if self.last_y is None:
            return None

        sigma = np.sqrt(np.diag(self.last_S))
        return np.abs(self.last_y) / sigma
