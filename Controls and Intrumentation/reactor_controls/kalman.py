import numpy as np

class KalmanFilter:
    def __init__(self, F, B, H, Q, R, x0, P0):
        self.F = F  # State transition matrix
        self.B = B  # Control input matrix
        self.H = H  # Observation matrix
        self.Q = Q  # Process noise cov.
        self.R = R  # Sensor noise cov.
        self.x = x0  # State estimate
        self.P = P0  # Covariance (uncertainty in x)

    def predict(self, u):
        """Predicts the next state estimate and covariance,
        using the control matrix/vector and process noise."""

        self.x = np.dot(self.F, self.x) + np.dot(self.B, u)
        self.P = np.dot(self.F, np.dot(self.P, self.F.T)) + self.Q

        return self.x

    def update(self, z):
        """Updates the state estimate and covariance based on measurement z,
        using the observation matrix and sensor noise."""
        
        # Innovation (actual - predicted)
        y = z - np.dot(self.H, self.x)

        # Innovation cov.
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R

        # Kalman gain (how much to trust measurement vs. prediction)
        K = np.dot(self.P, np.dot(self.H.T, np.linalg.inv(S)))

        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(K, np.dot(self.H, self.P))

        return self.x