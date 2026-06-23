import numpy as np


class Controller:
    def __init__(self, kp, ki, kd, rho_min=-5e-4, rho_max=5e-4):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.rho_min = rho_min
        self.rho_max = rho_max
        self.integral = 0.0
        self.previous_error = 0.0

    def update(self, desired_n, current_n, dt):
        error = desired_n - current_n
        derivative = (error - self.previous_error) / dt

        proposed_integral = self.integral + error * dt
        unconstrained_rho = (
            self.kp * error
            + self.ki * proposed_integral
            + self.kd * derivative
        )
        rho_rod = np.clip(unconstrained_rho, self.rho_min, self.rho_max)

        # Do not keep integrating error that would push an already-saturated rod farther.
        pushing_high = rho_rod == self.rho_max and error > 0.0
        pushing_low = rho_rod == self.rho_min and error < 0.0
        if not (pushing_high or pushing_low):
            self.integral = proposed_integral

        self.previous_error = error
        return rho_rod
