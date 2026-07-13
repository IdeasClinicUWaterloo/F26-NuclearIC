from model import ReactorModel

class EKF:
    def __init__(self, model, F, B, H, Q, R, x0, P0):

        self.model = model
        self.propagate = self.model.propagate

        self.H = H  # Observation matrix
        self.Q = Q  # Process noise cov.
        self.R = R  # Sensor noise cov.
        self.x = x0  # State estimate
        self.P = P0  # Covariance (uncertainty in x)

        