"""The control rod controller -- this is the main file to edit.

Right now it is a simple PID. To use your own instead, write a class with one
method:

    class MyController:
        def update(self, desired_n, current_n, dt):
            # desired_n : the power we want, where 1.0 is full rated power
            # current_n : the power we have right now
            #             (filtered by the EKF, unless you pass --no-filter)
            # dt        : seconds since this was last called
            return speed   # how fast to move the rods, in reactivity per second

then add it to CONTROLLERS at the bottom of this file and run:

    python run_scenario.py --scenario nominal --controller mine

Note that you say how fast to *move* the rods, not where to put them. Real
plants work this way: the controller drives a motor that winds the rods in or
out at some speed, and the reactivity you get is however far they have
travelled so far. simulation.py adds your speed up over time into a position
and caps it at the motor's top speed, so the rods cannot jump instantly no
matter how big a number you return.

That has a useful side effect. The rods keep creeping for as long as you ask
for any speed at all, so they carry on until the error is gone. Even with just
the P term switched on you end up with no leftover offset -- you do not need
the I term simply to close that last gap.
"""

import numpy as np

# Top speed of the motor that moves the rods, in reactivity per second. At
# this rate the rods take a couple of minutes to travel from one end of their
# range to the other, which is about right for the real thing.
MAX_ROD_SPEED = 2.5e-6


class Controller:
    def __init__(self, kp, ki, kd, max_speed=MAX_ROD_SPEED):
        self.kp = kp  # reacts to how wrong we are right now
        self.ki = ki  # reacts to how long we have been wrong
        self.kd = kd  # reacts to how fast the error is changing
        self.max_speed = max_speed

        self.integral = 0.0        # running total of past error
        self.previous_error = 0.0  # last step's error, for the D term

    def update(self, desired_n, current_n, dt):
        """Returns how fast to move the rods this timestep, in reactivity per
        second. Positive pulls them out, raising power; negative pushes them
        in, lowering it."""

        error = desired_n - current_n
        derivative = (error - self.previous_error) / dt
        proposed_integral = self.integral + error * dt

        speed = (
            self.kp * error
            + self.ki * proposed_integral
            + self.kd * derivative
        )
        clamped = np.clip(speed, -self.max_speed, self.max_speed)

        # The I term keeps a running total of past error. If the motor is
        # already flat out and still cannot keep up, that total just grows and
        # grows. Then when the error finally swings the other way, the
        # controller has to work through all of it before it responds at all,
        # so it sails straight past the target. This is called integral
        # windup. The fix: stop adding to the total whenever we are maxed out
        # and the error is still pushing the same way.
        maxed_out = clamped != speed
        if not (maxed_out and np.sign(error) == np.sign(clamped)):
            self.integral = proposed_integral

        self.previous_error = error
        return clamped


# Controllers that --controller can pick from. Register your own here.
# Each entry is a function that takes no arguments and returns a controller.
CONTROLLERS = {
    "pid": lambda: Controller(kp=3e-4, ki=0, kd=0),
}
