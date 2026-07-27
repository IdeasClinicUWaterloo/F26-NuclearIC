"""Simulated instrumentation: what the controller actually gets to see,
as opposed to the reactor's true state."""

import numpy as np


class Sensor:
    """One instrument channel. Reading = true value + bias + gaussian noise,
    unless it has been told to misbehave via set_fault()."""

    def __init__(self, sigma, bias=0.0, seed=None):
        self.sigma = sigma  # noise standard deviation
        self.bias = bias    # constant offset added to every reading

        self.fault = None
        self.fault_parameters = {}
        self.last_reading = None

        self.rng = np.random.default_rng(seed)

    def set_fault(self, fault_type, parameters=None):
        """Makes this sensor start misbehaving.

        "drift"   -- bias creeps by parameters["drift_rate"] per second
        "stuck"   -- freezes, repeating its last reading forever
        "dropout" -- reads NaN, i.e. the channel goes dead
        """

        self.fault = fault_type
        self.fault_parameters = parameters if parameters is not None else {}

    def step(self, dt):
        """Advances any time-dependent fault by one timestep."""

        if self.fault == "drift":
            self.bias += self.fault_parameters.get("drift_rate", 0.0) * dt

    def read(self, true_value):
        """Returns what this sensor reports for the given true value."""

        # A sensor stuck from the very first step has nothing to repeat yet,
        # so let it take one real sample and freeze on that.
        if self.fault == "stuck" and self.last_reading is not None:
            return self.last_reading

        if self.fault == "dropout":
            return np.nan

        reading = true_value + self.bias + self.rng.normal(0, self.sigma)
        self.last_reading = reading
        return reading


class SensorSuite:
    """Every instrument channel available to the controller."""

    def __init__(self):
        # 0.2% noise on power, roughly what a real excore neutron detector
        # manages. Turn it up if you want the filtering to matter more.
        self.power = Sensor(sigma=0.002)
        self.fuel_temp = Sensor(sigma=0.8)
        self.coolant_temp_1 = Sensor(sigma=0.5)
        self.coolant_temp_2 = Sensor(sigma=0.5)
        self.rod_reactivity = Sensor(sigma=0.0001)

    def _channels(self):
        return (self.power, self.fuel_temp, self.coolant_temp_1,
                self.coolant_temp_2, self.rod_reactivity)

    def step(self, dt):
        for sensor in self._channels():
            sensor.step(dt)

    def read_all(self, state, rho_rod):
        """Reads every channel. state is the reactor's true state vector:
        [n, C1..C6, T_fuel, T_c1, T_c2]."""

        return {
            "power": self.power.read(state[0]),
            "fuel_temp": self.fuel_temp.read(state[7]),
            "coolant_1_temp": self.coolant_temp_1.read(state[8]),
            "coolant_2_temp": self.coolant_temp_2.read(state[9]),
            "rod_reactivity": self.rod_reactivity.read(rho_rod),
        }
