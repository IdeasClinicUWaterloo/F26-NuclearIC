import numpy as np

class Sensor:
    """A class representing a generic sensor in a reactor control system."""

    def __init__(self, sigma, bias = 0.0, seed=None):
        """
        Initialize the sensor with a given sigma and bias.

        Parameters:
        sigma (float): The standard deviation of the sensor's noise.
        bias (float): The constant bias added to the sensor's readings.
        """

        self.sigma = sigma #magnitude of noise
        self.bias = bias #inherent bias in the sensor reading

        self.fault = None #fault state of the sensor, can be used to simulate sensor failures
        self.fault_parameters = None #parameters related to the fault, if any
        self.last_reading = None

        self.rng = np.random.default_rng(seed)
    
    def set_fault(self, fault_type, parameters=None):
        """
        Set a fault state for the sensor.

        Parameters:
        fault_type (str): The type of fault to simulate (e.g., "drift").
        parameters (dict): Additional parameters related to the fault.
        """

        self.fault = fault_type
        self.fault_parameters = parameters if parameters is not None else {}

    def step(self, dt):
        """
        Update the sensor's state over a time step.

        Parameters:
        dt (float): The time step over which to update the sensor.
        """

        if self.fault == "drift":
            
            # if drift rate is specified, get that number, otherwise 0
            drift_rate = self.fault_parameters.get("drift_rate", 0.0)
            self.bias += drift_rate * dt
    
    def read(self, true_value):
        """
        Simulate a sensor reading based on the true value, adding noise and bias.

        Parameters:
        true_value (float): The actual value that the sensor is measuring.

        Returns:
        float: The simulated sensor reading
        """

        if self.fault == "stuck":
            # If the sensor is stuck, return the last reading
            return self.last_reading
        
        if self.fault == "dropout":
            return np.nan # Simulate a dropout by returning NaN (Not a Number)
        
        reading = true_value + self.bias + self.rng.normal(0, self.sigma)
        self.last_reading = reading #store the last reading for reference

        return reading

class SensorSuite():
    def __init__(self):
        self.power = Sensor(sigma=0.005, bias=0.0)
        self.fuel_temp = Sensor(sigma=0.8, bias=0.0)
        self.coolant_temp_1 = Sensor(sigma=0.5, bias=0.0)
        self.coolant_temp_2 = Sensor(sigma=0.5, bias=0.0)
        self.rod_reactivity = Sensor(sigma=0.0001, bias=0.0)
    
    def step(self, dt):
        for s in (self.power, self.fuel_temp, self.coolant_temp_1,
                  self.coolant_temp_2, self.rod_reactivity):
            s.step(dt)
    
    def read_all(self, state, rho_rod):
        return{
            "power": self.power.read(state[0]),
            "fuel_temp": self.fuel_temp.read(state[7]),
            "coolant_1_temp": self.coolant_temp_1.read(state[8]),
            "coolant_2_temp": self.coolant_temp_2.read(state[9]),
            "rod_reactivity": self.rod_reactivity.read(rho_rod)
        }