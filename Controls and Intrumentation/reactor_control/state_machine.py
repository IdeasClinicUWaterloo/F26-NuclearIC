import numpy as np


class SafetySupervisor:
    """Safety state machine that sits between the controller and the
    reactor, watching raw instrumentation independently of the EKF, and
    overriding the commanded rod reactivity when the reactor approaches an
    unsafe condition.

    Deliberately independent of the estimator: a real protection system
    doesn't share its instrumentation chain with the control system, so a
    bug or fault in the EKF can't also disable safety.

    States, in increasing severity: NORMAL, WARNING, LIMITING, SCRAM,
    SHUTDOWN. SCRAM latches -- once triggered, the supervisor stays in
    SCRAM/SHUTDOWN for the rest of the run, matching how a real reactor
    protection system requires a deliberate reset rather than clearing
    itself the moment conditions look normal again.
    """

    def __init__(self, limits, rho_min, rho_max, limiting_rho_max=0.0,
                 scram_rho=-0.02, shutdown_power=0.05):
        """
        limits: dict keyed by channel name (e.g. "power", "fuel_temp",
        "coolant_temp"), each a dict with "warn", "limit", "scram"
        thresholds, e.g.:
            {"power": {"warn": 1.05, "limit": 1.10, "scram": 1.25}, ...}

        scram_rho is deliberately much more negative than rho_min: a real
        SCRAM drops separate shutdown rods with far more negative worth
        than the fine-control rods ever use, so it isn't just "hold at the
        controller's usual limit" -- it's a distinct emergency mechanism.
        """

        self.limits = limits
        self.rho_min = rho_min
        self.rho_max = rho_max
        self.limiting_rho_max = limiting_rho_max  # tighter cap while LIMITING
        self.scram_rho = scram_rho  # reactivity inserted once SCRAMmed
        self.shutdown_power = shutdown_power  # power below which SCRAM -> SHUTDOWN

        self.state = "NORMAL"
        self.scrammed = False
        self.triggers = []  # human-readable reasons from the most recent evaluate()

    def evaluate(self, readings):
        """Updates and returns the current safety state from raw
        (unfiltered) instrumentation. `readings` is a dict keyed the same
        way as `limits`."""

        self.triggers = []
        worst = "NORMAL"
        severity = {"NORMAL": 0, "WARNING": 1, "LIMITING": 2, "SCRAM": 3}

        for name, value in readings.items():
            lim = self.limits.get(name)
            if lim is None:
                continue

            if value > lim["scram"]:
                self.triggers.append(f"{name}={value:.3f} exceeds SCRAM limit {lim['scram']:.3f}")
                level = "SCRAM"
            elif value > lim["limit"]:
                level = "LIMITING"
            elif value > lim["warn"]:
                level = "WARNING"
            else:
                level = "NORMAL"

            if severity[level] > severity[worst]:
                worst = level

        if worst == "SCRAM":
            self.scrammed = True

        if self.scrammed:
            power = readings.get("power", 1.0)
            self.state = "SHUTDOWN" if power < self.shutdown_power else "SCRAM"
        else:
            self.state = worst

        return self.state

    def apply(self, commanded_rho):
        """Overrides the controller's commanded rod reactivity based on the
        current safety state."""

        if self.state in ("SCRAM", "SHUTDOWN"):
            return self.scram_rho  # emergency shutdown insertion, not just rho_min

        if self.state == "LIMITING":
            return np.clip(commanded_rho, self.rho_min, self.limiting_rho_max)

        return np.clip(commanded_rho, self.rho_min, self.rho_max)
