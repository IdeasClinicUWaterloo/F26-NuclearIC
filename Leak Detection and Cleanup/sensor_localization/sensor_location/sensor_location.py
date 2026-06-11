import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

PORT = "COM11"
BAUD = 115200
WINDOW = 200
AVG_WINDOW = 50   # ~1 second at 50 Hz
TOP_K = 20        # use the strongest 20 samples in each 1-second window

# -----------------------------
# Calibration (difference-based)
# -----------------------------
CALIBRATION = [-1000.12, -300.37, -123.19, -60 , 2.475, 454.2]
CAL_POSITIONS = [0, 20, 40, 60, 80, 100]

NO_VIB_THRESHOLD = 70   # minimum total signal for a sample to count as "strong"

cal_vals = np.array(CALIBRATION, dtype=float)
positions = np.array(CAL_POSITIONS, dtype=float)

# sort calibration
idx = np.argsort(cal_vals)
cal_vals = cal_vals[idx]
positions = positions[idx]

def estimate_position(v1, v2):
    diff = v1 - v2
    pos = np.interp(diff, cal_vals, positions)
    return diff, pos

# -----------------------------
# Serial
# -----------------------------
ser = serial.Serial(PORT, BAUD, timeout=0.05)
ser.reset_input_buffer()

# raw plotting buffers
s1 = deque([0.0] * WINDOW, maxlen=WINDOW)
s2 = deque([0.0] * WINDOW, maxlen=WINDOW)

# 1-second buffers
s1_win = deque(maxlen=AVG_WINDOW)
s2_win = deque(maxlen=AVG_WINDOW)

# -----------------------------
# Plot
# -----------------------------
plt.ion()
fig, ax = plt.subplots(figsize=(10, 5))
line1, = ax.plot(range(WINDOW), s1, label="sensor1")
line2, = ax.plot(range(WINDOW), s2, label="sensor2")

ax.set_title("Live Sensor Output")
ax.set_xlabel("Sample")
ax.set_ylabel("Value")
ax.legend()
ax.grid(True)

pos_text = ax.text(
    0.02, 0.95, "Position: -- %",
    transform=ax.transAxes,
    verticalalignment="top",
    fontsize=12,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)

diff_text = ax.text(
    0.02, 0.87, "Difference: --",
    transform=ax.transAxes,
    verticalalignment="top",
    fontsize=11,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)

peak_text = ax.text(
    0.02, 0.79, "Peaks used: --",
    transform=ax.transAxes,
    verticalalignment="top",
    fontsize=11,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)

update_count = 0

try:
    while True:
        raw = None

        # keep only newest serial line
        while ser.in_waiting:
            raw = ser.readline().decode(errors="ignore").strip()

        if not raw:
            plt.pause(0.001)
            continue

        if "Sensor1" in raw or "Sensor2" in raw or "Starting" in raw:
            print(raw)
            continue

        if raw.lower() == "vib1,vib2":
            print(raw)
            continue

        parts = raw.split(",")
        if len(parts) != 2:
            continue

        try:
            v1 = float(parts[0])
            v2 = float(parts[1])
        except ValueError:
            continue

        # raw plotting buffers
        s1.append(v1)
        s2.append(v2)

        # rolling 1-second window
        s1_win.append(v1)
        s2_win.append(v2)

        diff = None
        pos = None
        peaks_used = 0

        # compute position from top peaks only when window is full
        if len(s1_win) == AVG_WINDOW:
            v1_arr = np.array(s1_win)
            v2_arr = np.array(s2_win)
            total = v1_arr + v2_arr

            # keep only strong samples
            strong_idx = np.where(total > NO_VIB_THRESHOLD)[0]

            if len(strong_idx) > 0:
                # sort strong samples by total signal strength
                strong_totals = total[strong_idx]
                order = np.argsort(strong_totals)

                # take top-k strongest among the strong samples
                k = min(TOP_K, len(strong_idx))
                chosen_idx = strong_idx[order[-k:]]

                avg_v1 = np.mean(v1_arr[chosen_idx])
                avg_v2 = np.mean(v2_arr[chosen_idx])

                if(k > 10):
                    diff, pos = estimate_position(avg_v1, avg_v2)
                else:
                    diff, pos = None, None
                peaks_used = k

        update_count += 1
        if update_count % 3 == 0:
            line1.set_ydata(s1)
            line2.set_ydata(s2)

            current_max = max(max(s1), max(s2), 1.0)
            ax.set_ylim(0, 1500)

            if pos is not None:
                pos_text.set_text(f"Position: {pos:.1f}%")
                diff_text.set_text(f"Diff: {diff:.1f}")
                peak_text.set_text(f"Peaks used: {peaks_used}")
            else:
                pos_text.set_text("Position: -- % (no vibration / warming)")
                diff_text.set_text("Diff: --")
                peak_text.set_text("Peaks used: 0")

            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            plt.pause(0.001)

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    ser.close()
    plt.ioff()
    plt.show()