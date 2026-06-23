class Controller:
    def __init__(self, kp, ki, kd):
        self.integral = 0
        self.previous_error = 0
        self.kp = kp
        self.ki = ki
        self.kd = kd

    def update(self, desired_n, current_n, dt):
        error = desired_n - current_n
        self.integral += error*dt
        derivative = (error - self.previous_error)/dt

        #we are controlling reactivty by manipulating control rod position

        rho_rod = self.kp * error + self.ki * self.integral + self.kd * derivative

        if rho_rod > 0.1:
            print("Warning: Control rod reactivity limit exceeded. Clamping to 0.1.")
            rho_rod = 0.1

        self.previous_error = error

        return rho_rod
