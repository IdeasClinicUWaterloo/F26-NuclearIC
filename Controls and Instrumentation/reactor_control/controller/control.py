"""Baseline control-rod controller and controller registry.

A controller implements ``update(desired_n, current_n, dt)`` and returns rod
speed in reactivity per second. ``Simulation`` integrates that speed into rod
position and enforces the drive and travel limits.
"""

import numpy as np


# Rod-drive speed limit, in reactivity per second.
MAX_ROD_SPEED = 2.5e-6


class Controller:
    def __init__(self, kp, ki, kd, max_speed=MAX_ROD_SPEED):
        values = np.asarray([kp, ki, kd, max_speed], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("PID gains and max_speed must be finite")
        if max_speed <= 0:
            raise ValueError("max_speed must be positive")

        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.max_speed = float(max_speed)

        self.integral = 0.0
        self.previous_error = None

    def update(self, desired_n, current_n, dt):
        """Return rod speed; positive speed withdraws rods and raises power."""

        if not np.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be a positive finite number")
        if not np.isfinite(desired_n) or not np.isfinite(current_n):
            raise ValueError("desired_n and current_n must be finite")

        error = desired_n - current_n
        derivative = (
            0.0
            if self.previous_error is None
            else (error - self.previous_error) / dt
        )
        proposed_integral = self.integral + error * dt

        speed = (
            self.kp * error
            + self.ki * proposed_integral
            + self.kd * derivative
        )
        clamped = float(np.clip(speed, -self.max_speed, self.max_speed))

        # Stop integrating when the error would push a saturated drive farther
        # into saturation. The integral can still unwind in the other direction.
        maxed_out = clamped != speed
        if not (maxed_out and np.sign(error) == np.sign(clamped)):
            self.integral = proposed_integral

        self.previous_error = error
        return clamped


# Register controller factories here to expose them through ``--controller``.
CONTROLLERS = {
    "pid": lambda: Controller(kp=3e-4, ki=0, kd=0),
}
