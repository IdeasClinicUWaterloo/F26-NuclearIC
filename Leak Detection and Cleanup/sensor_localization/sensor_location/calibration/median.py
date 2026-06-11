import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Load data
# -----------------------------
data = np.loadtxt("100_percent.txt", delimiter=",")

s1 = data[:, 0]
s2 = data[:, 1]

# -----------------------------
# Compute DIFFERENCE
# -----------------------------
diff = s1 - s2   # raw difference

# -----------------------------
# Clean data (remove bad points)
# -----------------------------
total = s1 + s2
valid = total > 30      # IMPORTANT: use total threshold, not arbitrary values

diff = diff[valid]

# Optional: remove extreme spikes (use percentiles, not fixed numbers)
low, high = np.percentile(diff, [5, 95])
diff = diff[(diff > low) & (diff < high)]

# -----------------------------
# Compute calibration value
# -----------------------------
d_median = np.median(diff)
d_mean   = np.mean(diff)

print("Median difference (recommended):", d_median)
print("Mean difference:", d_mean)

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(10,4))
plt.plot(diff, label="s1 - s2")
plt.axhline(d_median, linestyle='--', label=f"median = {d_median:.2f}")

plt.title("Difference over time (position)")
plt.xlabel("Sample")
plt.ylabel("Difference (s1 - s2)")
plt.legend()
plt.grid()

plt.show()