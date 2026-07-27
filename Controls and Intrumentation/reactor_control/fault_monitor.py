class FaultMonitor:
    """Flags a measurement channel as a suspected sensor fault using the
    EKF's own innovation (measurement residual): if a channel's normalized
    innovation (how many sigma away the reading was from what the filter
    expected) stays large for many consecutive steps, that's the signature
    of something disagreeing with the model, not just ordinary noise.

    A single large residual is expected from noise now and then -- it's a
    *sustained* run of them that's suspicious, which is why this requires
    `consecutive_required` steps in a row rather than any single threshold
    crossing.

    Isolation: a real unmodeled disturbance perturbs the whole coupled
    system, so several channels tend to go anomalous together. One sensor
    actually failing looks different -- just that one channel disagreeing
    while the rest still track fine. So a channel is only confirmed as a
    faulted *sensor* when it's the sole channel in a sustained streak;
    multiple simultaneous streaks are reported as a suspected disturbance
    (model mismatch) instead of blamed on any one sensor.
    """

    def __init__(self, channel_names, threshold=2.5, consecutive_required=20):
        self.channel_names = channel_names
        self.threshold = threshold
        self.consecutive_required = consecutive_required
        self.streaks = {name: 0 for name in channel_names}
        self.flagged = {name: False for name in channel_names}
        self.disturbance_suspected = False

    def update(self, normalized_innovation):
        """normalized_innovation: array matching channel_names, from
        EKF.normalized_innovation(). Returns the current flagged dict; also
        sets self.disturbance_suspected for the multi-channel case."""

        if normalized_innovation is None:
            return dict(self.flagged)

        for name, value in zip(self.channel_names, normalized_innovation):
            if value > self.threshold:
                self.streaks[name] += 1
            else:
                self.streaks[name] = 0

        active = [name for name, s in self.streaks.items() if s >= self.consecutive_required]

        if len(active) == 1:
            self.flagged[active[0]] = True
            self.disturbance_suspected = False
        elif len(active) > 1:
            self.disturbance_suspected = True

        return dict(self.flagged)

    def reset(self, name):
        """Clears a fault flag -- e.g. after an operator investigates and
        the sensor is replaced or recalibrated."""

        self.flagged[name] = False
        self.streaks[name] = 0
