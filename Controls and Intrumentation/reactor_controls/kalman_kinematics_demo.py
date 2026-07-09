import numpy as np
import matplotlib.pyplot as plt

from kalman import KalmanFilter
from sensors import Sensor

# --- Setup ---
dt = 0.05
duration = 10.0
steps = int(duration / dt)

true_velocity = 1.0
true_x = np.array([[0.0], [true_velocity]])  # [position, velocity]

sensor = Sensor(sigma = 0.1, seed = 42)

F = np.array([[1.0, dt],
     [0, 1.0]])
B = np.zeros((2, 1))  # no control input for now -- leave this as-is
H = np.array([[1.0, 0.0]])  # TODO: 1x2, picks out position only
Q = np.eye(2) * 0.01
R = np.array([[0.2]])

x0 = np.array([[0.0], [0.0]])  # deliberately wrong guess, so you can see convergence
P0 = np.eye(2) * 10.0

kf = KalmanFilter(F, B, H, Q, R, x0, P0)  # TODO: KalmanFilter(F, B, H, Q, R, x0, P0)

t_hist, true_pos_hist, true_vel_hist = [], [], []
meas_hist, est_pos_hist, est_vel_hist = [], [], []

meas_error, pos_error, vel_error = [], [], []
pos_std_hist, vel_std_hist = [], []

for i in range(steps):
    t = i * dt

    # advance true_x forward by one dt 
    true_x = F @ true_x
    
    # get a noisy reading of true_x's position from sensor.read, located at row 0 column 0
    z = sensor.read(true_x[0, 0])

    kf.predict(np.array([[0.0]]))

    kf.update(z)

    # TODO: append t, true position, true velocity, measurement, kf estimated position, kf estimated velocity
    t_hist.append(t)
    true_pos_hist.append(true_x[0, 0])
    true_vel_hist.append(true_x[1, 0])

    meas_hist.append(z)
    est_pos_hist.append(kf.x[0, 0])
    est_vel_hist.append(kf.x[1, 0])
    pos_std_hist.append(np.sqrt(kf.P[0, 0]))
    vel_std_hist.append(np.sqrt(kf.P[1, 1]))

# --- Report ---
# TODO: print RMSE of raw measurement vs true position, and filtered estimate vs true position/velocity
    meas_rmse = np.sqrt(np.mean((np.array(true_pos_hist[:i + 1]) - np.array(meas_hist[:i + 1]))**2))
    pos_rmse = np.sqrt(np.mean((np.array(true_pos_hist[:i + 1]) - np.array(est_pos_hist[:i + 1]))**2))
    vel_rmse = np.sqrt(np.mean((np.array(true_vel_hist[:i + 1]) - np.array(est_vel_hist[:i + 1]))**2))

    meas_error.append(meas_rmse)

    pos_error.append(pos_rmse)

    vel_error.append(vel_rmse)

meas_rmse = np.sqrt(np.mean((np.array(true_pos_hist) - np.array(meas_hist))**2))
pos_rmse = np.sqrt(np.mean((np.array(true_pos_hist) - np.array(est_pos_hist))**2))
vel_rmse = np.sqrt(np.mean((np.array(true_vel_hist) - np.array(est_vel_hist))**2))

print(f"RMSE of raw measurement vs true position: {meas_rmse:.4f}")
print(f"RMSE of filtered estimate vs true position: {pos_rmse:.4f}")
print(f"RMSE of filtered estimate vs true velocity: {vel_rmse:.4f}")


# --- Plot ---
t_arr = np.array(t_hist)
pos_std_arr = np.array(pos_std_hist)
vel_std_arr = np.array(vel_std_hist)
est_pos_arr = np.array(est_pos_hist)
est_vel_arr = np.array(est_vel_hist)

fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

ax = axes[0]
ax.plot(t_hist, true_pos_hist, label="True position", color="black", linewidth=1.5)
ax.scatter(t_hist, meas_hist, label="Noisy measurement", color="gray", s=8, alpha=0.5)
ax.plot(t_hist, est_pos_hist, label="KF estimate", color="tab:blue", linewidth=2)
ax.fill_between(t_arr, est_pos_arr - 2 * pos_std_arr, est_pos_arr + 2 * pos_std_arr,
                 color="tab:blue", alpha=0.15, label="±2σ estimate uncertainty")
ax.set_ylabel("Position (m)")
ax.set_title("Position: truth vs. noisy sensor vs. Kalman estimate")
ax.legend(loc="upper left")
ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(t_hist, true_vel_hist, label="True velocity", color="black", linewidth=1.5)
ax.plot(t_hist, est_vel_hist, label="KF estimate (never directly measured)",
        color="tab:orange", linewidth=2)
ax.fill_between(t_arr, est_vel_arr - 2 * vel_std_arr, est_vel_arr + 2 * vel_std_arr,
                 color="tab:orange", alpha=0.15, label="±2σ estimate uncertainty")
ax.set_ylabel("Velocity (m/s)")
ax.set_title("Velocity: hidden state, reconstructed purely from the model")
ax.legend(loc="upper left")
ax.grid(alpha=0.3)

ax = axes[2]
ax.plot(t_hist, meas_error, label="Raw measurement RMSE", color="gray", linewidth=1.5)
ax.plot(t_hist, pos_error, label="Filtered position RMSE", color="tab:blue", linewidth=2)
ax.plot(t_hist, vel_error, label="Filtered velocity RMSE", color="tab:orange", linewidth=2)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Running RMSE")
ax.set_title("Estimation error over time (convergence)")
ax.legend(loc="upper right")
ax.grid(alpha=0.3)

plt.tight_layout()
plt.show()