import numpy as np
import matplotlib.pyplot as plt

# load your file
data = np.loadtxt("nothing.txt", delimiter=",")

# split columns
s1 = data[:,0]
s2 = data[:,1]

# compute ratio (key for position)
ratio = s1 / (s1 + s2 + 1e-6)  # avoid divide by zero

# -----------------------------
# Plot everything in one window
# -----------------------------
fig, axs = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

# Top: raw sensor values
axs[0].plot(s1, label="sensor1")
axs[0].plot(s2, label="sensor2")
axs[0].set_title("Raw Sensor Values")
axs[0].legend()
axs[0].grid()

# Bottom: ratio (this is what matters)
axs[1].plot(ratio, label="L / (L + R)")
axs[1].set_title("Position Ratio")
axs[1].set_ylim(0,1)
axs[1].legend()
axs[1].grid()

plt.xlabel("Sample")
plt.tight_layout()
plt.show()