"""Extended Kalman Filter: turns noisy sensor readings into a best guess at
what the reactor is actually doing.

This is an advanced file. You can use it without reading it, and still build a
strong project. If you do want to understand it, read the visual explainer
linked in the README first.

The short version. Every timestep the filter does two things:

    predict -- run the reactor model forward to work out where the reactor
               should be a moment later
    update  -- compare that guess against the sensors, and shift it partway
               toward what they say

How far it shifts depends on which one it trusts more, and that is what the Q
and R settings control. Note it tracks 10 quantities (power, six precursor
groups, three temperatures) from only 4 sensors, so it is also filling in
values that nothing measures directly.
"""

import numpy as np
from scipy.linalg import expm


class EKF:
    def __init__(self, model, H, Q, R, x0, P0, dt, jac_eps=1e-6):

        self.model = model

        self.H = H    # which state entries the sensors actually read
        self.Q = Q    # how much we distrust the model   (bigger = trust it less)
        self.R = R    # how much we distrust the sensors (bigger = trust them less)
        self.x = x0   # current best guess at the reactor state
        self.P = P0   # how unsure we are about that guess
        self.dt = dt  # length of one timestep, in seconds
        self.jac_eps = jac_eps  # how hard to nudge each state when measuring slopes

        # From the most recent update(): how far each sensor reading landed
        # from what the filter expected, and how big a gap is normal. Kept so
        # you can build fault detection on top -- see normalized_innovation().
        self.last_y = None
        self.last_S = None

    def _numerical_jacobian(self, rho_rod):
        """Works out how sensitive the reactor's rate of change is to each of
        the 10 states, by nudging each one up and down and seeing how much the
        answer moves.

        The filter needs this to know how fast its uncertainty grows. Doing it
        by nudging means nobody has to differentiate the reactor equations by
        hand.
        """

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
        """Steps the guess forward one timestep and grows the uncertainty to
        match, since the longer we go without checking a sensor, the less sure
        we are."""

        A = self._numerical_jacobian(rho_rod)

        # expm() here, rather than the usual (I + A*dt) shortcut. The neutron
        # population settles in well under a millisecond, far quicker than our
        # 0.1 s timestep, and that shortcut goes unstable when something moves
        # that fast -- the numbers blow up instead of settling down. expm
        # handles fast-changing quantities properly.
        F = expm(A * self.dt)

        self.x = self.model.propagate(self.x, rho_rod, self.dt)
        self.P = F @ self.P @ F.T + self.Q

        return self.x

    def update(self, z, H=None, R=None):
        """Pulls the guess toward the sensor readings in z.

        y is the gap between what we measured and what we expected. K decides
        how much of that gap to act on: near 0 means stick with the model,
        near 1 means believe the sensors.

        H and R cover all four sensors by default. Pass smaller ones to use
        only some of them -- that is how a dead sensor is handled, by leaving
        its row out and carrying on with the ones that still work.
        """

        H = self.H if H is None else H
        R = self.R if R is None else R

        y = z - H @ self.x
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = self.P - K @ H @ self.P

        self.last_y = y
        self.last_S = S

        return self.x

    def normalized_innovation(self):
        """How far each sensor reading sat from what the filter expected,
        measured in multiples of the gap you would normally see anyway. A
        value around 1 is unremarkable; 5 means that reading is well out of
        line.

        Nothing uses this yet. It is a reasonable starting point if you want
        to build fault detection, but be warned that it is not as simple as
        picking a cut-off. The filter quietly absorbs a slow drift, so the
        number stays small even while the sensor goes badly wrong, and one
        broken sensor can drag a healthy one off with it. See "Known Gaps" in
        the README.
        """

        if self.last_y is None:
            return None

        sigma = np.sqrt(np.diag(self.last_S))
        return np.abs(self.last_y) / sigma
