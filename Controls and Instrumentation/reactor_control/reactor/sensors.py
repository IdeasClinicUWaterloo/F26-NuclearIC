"""Noisy reactor instrumentation with optional fault injection."""

import numpy as np


class Sensor:
    """A noisy instrument channel with optional drift, stuck, or dropout faults."""

    def __init__(self, sigma, bias=0.0, seed=None):
        if not np.isfinite(sigma) or sigma < 0:
            raise ValueError("sigma must be a finite, non-negative number")
        if not np.isfinite(bias):
            raise ValueError("bias must be finite")

        self.sigma = float(sigma)
        self.bias = float(bias)
        self.fault = None
        self.fault_parameters = {}
        self.last_reading = None
        self.rng = np.random.default_rng(seed)

    def set_fault(self, fault_type, parameters=None):
        """Enable a supported sensor fault.

        ``drift`` changes bias by ``drift_rate`` per second, ``stuck`` repeats
        the last sample, and ``dropout`` reports NaN.
        """

        if fault_type not in {"drift", "stuck", "dropout"}:
            raise ValueError(f"Unsupported sensor fault: {fault_type!r}")

        parameters = {} if parameters is None else dict(parameters)
        if fault_type == "drift":
            drift_rate = parameters.get("drift_rate", 0.0)
            if not np.isfinite(drift_rate):
                raise ValueError("drift_rate must be finite")

        self.fault = fault_type
        self.fault_parameters = parameters

    def step(self, dt):
        """Advance a time-dependent fault by ``dt`` seconds."""

        if not np.isfinite(dt) or dt < 0:
            raise ValueError("dt must be a finite, non-negative number")

        if self.fault == "drift":
            self.bias += self.fault_parameters.get("drift_rate", 0.0) * dt

    def read(self, true_value):
        """Return a noisy, biased reading of ``true_value``."""

        # A newly stuck sensor needs one sample before it has a value to repeat.
        if self.fault == "stuck" and self.last_reading is not None:
            return self.last_reading

        if self.fault == "dropout":
            return np.nan

        reading = true_value + self.bias + self.rng.normal(0, self.sigma)
        self.last_reading = reading
        return reading


class SensorSuite:
    """Every instrument channel available to the controller."""

    def __init__(self, seed=0):
        channel_seeds = np.random.SeedSequence(seed).spawn(5)

        self.power = Sensor(sigma=0.002, seed=channel_seeds[0])
        self.fuel_temp = Sensor(sigma=0.8, seed=channel_seeds[1])
        self.coolant_temp_1 = Sensor(sigma=0.5, seed=channel_seeds[2])
        self.coolant_temp_2 = Sensor(sigma=0.5, seed=channel_seeds[3])
        self.rod_reactivity = Sensor(sigma=0.0001, seed=channel_seeds[4])

    def _channels(self):
        return (
            self.power,
            self.fuel_temp,
            self.coolant_temp_1,
            self.coolant_temp_2,
            self.rod_reactivity,
        )

    def step(self, dt):
        for sensor in self._channels():
            sensor.step(dt)

    def read_all(self, state, rho_rod):
        """Read all channels from the true ten-element reactor state."""

        return {
            "power": self.power.read(state[0]),
            "fuel_temp": self.fuel_temp.read(state[7]),
            "coolant_1_temp": self.coolant_temp_1.read(state[8]),
            "coolant_2_temp": self.coolant_temp_2.read(state[9]),
            "rod_reactivity": self.rod_reactivity.read(rho_rod),
        }
