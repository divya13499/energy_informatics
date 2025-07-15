class PIDController:
    def __init__(self, kp, ki, kd, initial_time=0, max_cumulative=None, min_cumulative=None, min_integral=None, max_integral=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.integral = 0.0
        self.previous_error = 0.0
        self.current_value = 0.0
        self.cumulative_value = 0.0

        self.last_time = initial_time

        self.max_integral = max_integral
        self.min_integral = min_integral
        self.max_cumulative = max_cumulative
        self.min_cumulative = min_cumulative

    def step(self, current_time: int, reference_value: float, process_value: float):
        error = reference_value - process_value

        # Determine time difference (assume 1 on first call or bad input)
        delta_time = current_time - self.last_time
        if delta_time <= 0:
            delta_time = 1

        # --- Proportional ---
        p_term = self.kp * error

        # --- Integral ---
        self.integral += error * delta_time
        if self.max_integral is not None:
            self.integral = min(self.integral, self.max_integral)
        if self.min_integral is not None:
            self.integral = max(self.integral, self.min_integral)
        i_term = self.ki * self.integral

        # --- Derivative ---
        d_term = self.kd * (error - self.previous_error) / delta_time if delta_time > 0 else 0.0

        # --- Output ---
        self.current_value = p_term + i_term + d_term

        # --- Cumulative value ---
        self.cumulative_value += self.current_value
        if self.max_cumulative is not None:
            self.cumulative_value = min(self.cumulative_value, self.max_cumulative)
        if self.min_cumulative is not None:
            self.cumulative_value = max(self.cumulative_value, self.min_cumulative)

        # Update state
        self.previous_error = error
        self.last_time = current_time

    def get_current_value(self):
        return self.current_value

    def get_cumulative_value(self):
        return self.cumulative_value
