import numpy as np


class SafetySupervisor:
    """Clamp or override rod commands when raw readings cross safety limits.

    The supervisor bypasses the EKF, so an estimator failure cannot hide an
    unsafe reading. SCRAM remains latched for the rest of the run.
    """

    def __init__(self, limits, rho_min, rho_max, limiting_rho_max=0.0,
                 scram_rho=-0.02, shutdown_power=0.05):
        """Create a supervisor from per-channel warn, limit, and SCRAM levels.

        ``scram_rho`` represents separate shutdown rods, so it may be more
        negative than the normal control-rod range.
        """

        for channel, thresholds in limits.items():
            missing = {"warn", "limit", "scram"} - thresholds.keys()
            if missing:
                raise ValueError(f"{channel} is missing limits: {sorted(missing)}")
            warn, limit, scram = (
                thresholds["warn"], thresholds["limit"], thresholds["scram"]
            )
            if not np.isfinite([warn, limit, scram]).all():
                raise ValueError(f"{channel} limits must be finite")
            if not warn < limit < scram:
                raise ValueError(
                    f"{channel} limits must satisfy warn < limit < scram"
                )

        if not np.isfinite([
            rho_min,
            rho_max,
            limiting_rho_max,
            scram_rho,
            shutdown_power,
        ]).all():
            raise ValueError("reactivity limits and shutdown_power must be finite")
        if not rho_min < rho_max:
            raise ValueError("rho_min must be less than rho_max")
        if not rho_min <= limiting_rho_max <= rho_max:
            raise ValueError(
                "limiting_rho_max must be within the control-rod range"
            )
        if shutdown_power < 0:
            raise ValueError("shutdown_power cannot be negative")

        self.limits = limits
        self.rho_min = rho_min
        self.rho_max = rho_max
        self.limiting_rho_max = limiting_rho_max
        self.scram_rho = scram_rho
        self.shutdown_power = shutdown_power

        self.state = "NORMAL"
        self.scrammed = False
        self.triggers = []

    def evaluate(self, readings):
        """Update the safety state from raw readings keyed like ``limits``."""

        self.triggers = []
        worst = "NORMAL"
        severity = {"NORMAL": 0, "WARNING": 1, "LIMITING": 2, "SCRAM": 3}

        for name, value in readings.items():
            limits = self.limits.get(name)
            if limits is None:
                continue

            if not np.isfinite(value):
                level = "WARNING"
                self.triggers.append(f"{name} reading is unavailable")
            elif value >= limits["scram"]:
                level = "SCRAM"
                self.triggers.append(
                    f"{name}={value:.3f} reached SCRAM limit "
                    f"{limits['scram']:.3f}"
                )
            elif value >= limits["limit"]:
                level = "LIMITING"
                self.triggers.append(
                    f"{name}={value:.3f} reached limit {limits['limit']:.3f}"
                )
            elif value >= limits["warn"]:
                level = "WARNING"
                self.triggers.append(
                    f"{name}={value:.3f} reached warning limit "
                    f"{limits['warn']:.3f}"
                )
            else:
                level = "NORMAL"

            if severity[level] > severity[worst]:
                worst = level

        if worst == "SCRAM":
            self.scrammed = True

        if self.scrammed:
            power = readings.get("power", 1.0)
            if self.state == "SHUTDOWN":
                return self.state
            self.state = (
                "SHUTDOWN"
                if np.isfinite(power) and power < self.shutdown_power
                else "SCRAM"
            )
        else:
            self.state = worst

        return self.state

    def apply(self, commanded_rho):
        """Apply the current state's control-rod limit or SCRAM override."""

        if self.state in ("SCRAM", "SHUTDOWN"):
            return self.scram_rho

        if self.state == "LIMITING":
            return np.clip(commanded_rho, self.rho_min, self.limiting_rho_max)

        return np.clip(commanded_rho, self.rho_min, self.rho_max)
