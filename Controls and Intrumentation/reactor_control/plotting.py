import numpy as np
import matplotlib.pyplot as plt


def _plot_power(simulator):
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)

    ax.plot(simulator.time_steps, simulator.n_current_values, label="True neutron population", color="black")
    ax.scatter(simulator.time_steps, simulator.n_measured_values, label="Raw noisy reading",
               color="gray", s=6, alpha=0.4)
    ax.plot(simulator.time_steps, simulator.n_estimated_values, label="EKF estimate", color="tab:blue")
    ax.plot(
        simulator.time_steps,
        simulator.n_desired_values,
        "--",
        label="Desired neutron population",
    )
    for name in ("power", "fuel_temp", "coolant_1_temp", "coolant_2_temp"):
        first_flagged_t = next(
            (simulator.control_times[i] for i, flags in enumerate(simulator.fault_flag_history)
             if flags.get(name)),
            None,
        )
        if first_flagged_t is not None:
            ax.axvline(first_flagged_t, color="purple", linestyle=":", alpha=0.8)
            ax.text(first_flagged_t, ax.get_ylim()[1], f" fault: {name}",
                    color="purple", fontsize=8, va="top")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Normalized power")
    ax.set_title("Closed-Loop Reactor Power: true vs. measured vs. filtered")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_rod_command(simulator):
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)

    ax.plot(
        simulator.control_times,
        simulator.commanded_rho_values,
        label="Controller-commanded rho",
        color="tab:red",
        linestyle="--",
        alpha=0.7,
    )
    ax.plot(
        simulator.control_times,
        simulator.control_values,
        label="Actually-applied rho",
        color="orange",
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Reactivity, rho (dk/k)")
    ax.set_title("Control-Rod Command: controller request vs. what was actually applied")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_thermal_feedback(simulator):
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)

    ax.plot(
        simulator.time_steps[1:],
        simulator.feedback_rho_values,
        label="Thermal reactivity",
        color="green",
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Reactivity, rho (dk/k)")
    ax.set_title("Thermal Reactivity Feedback")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_estimation_error(simulator):
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)

    measured_err = np.abs(np.array(simulator.n_measured_values) - np.array(simulator.n_current_values))
    estimated_err = np.abs(np.array(simulator.n_estimated_values) - np.array(simulator.n_current_values))
    ax.plot(simulator.time_steps, measured_err, label="Raw measurement error", color="gray")
    ax.plot(simulator.time_steps, estimated_err, label="EKF estimate error", color="tab:blue")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("|error|")
    ax.set_title("Power Estimation Error: raw vs. filtered")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_safety_state(simulator):
    fig, ax = plt.subplots(figsize=(10, 3.5), constrained_layout=True)

    state_levels = {"NORMAL": 0, "WARNING": 1, "LIMITING": 2, "SCRAM": 3, "SHUTDOWN": 4}
    state_values = [state_levels[s] for s in simulator.safety_states]
    ax.step(simulator.control_times, state_values, where="post", color="crimson")
    ax.set_yticks(list(state_levels.values()), list(state_levels.keys()))
    ax.set_ylim(-0.5, 4.5)
    ax.set_xlabel("Time (s)")
    ax.set_title("Safety Supervisor State")
    ax.grid()


def _plot_temperatures(simulator):
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)

    ax.plot(simulator.time_steps, simulator.fuel_temp_values, label="Fuel temp (K)", color="firebrick")
    ax.plot(simulator.time_steps, simulator.coolant_temp_avg_values, label="Coolant temp avg (K)", color="teal")
    ax.axhline(simulator.safety.limits["fuel_temp"]["scram"], color="firebrick", linestyle=":", alpha=0.6, label="Fuel SCRAM limit")
    ax.axhline(simulator.safety.limits["coolant_temp"]["scram"], color="teal", linestyle=":", alpha=0.6, label="Coolant SCRAM limit")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (K)")
    ax.set_title("True Temperatures vs. Safety Limits")
    ax.legend(fontsize=8, framealpha=0.9)
    ax.grid()


def plot_simulation(simulator):
    """Renders the reactor run as separate, individually-sized figures --
    power tracking, control-rod command, thermal feedback, estimation
    error, safety supervisor state, and true temperatures vs. safety
    limits -- rather than one cramped stack of subplots."""

    _plot_power(simulator)
    _plot_rod_command(simulator)
    _plot_thermal_feedback(simulator)
    _plot_estimation_error(simulator)
    _plot_safety_state(simulator)
    _plot_temperatures(simulator)
    plt.show()
