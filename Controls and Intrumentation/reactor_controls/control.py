class Controller:
    def __init__(self, kp, ki, kd):
        self.integral = 0
        self.previous_error = 0
        self.kp = kp
        self.ki = ki
        self.kd = kd

    def update(self, setpoint, pv, dt):
        error = setpoint - pv
        self.integral += error*dt
        derivative = (error - self.previous_error)/dt
        control = self.kp*error + self.ki*self.integral + self.kd*derivative

        self.previous_error = error

        return control