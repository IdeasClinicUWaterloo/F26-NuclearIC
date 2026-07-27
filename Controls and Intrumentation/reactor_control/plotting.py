"""Plots for a completed Simulation run. Each view opens as its own figure
so nothing gets squashed; add your own here for the demo.

Click any legend entry to show/hide that line. Handy when the raw sensor
cloud is burying the trace you actually want to look at.
"""

import numpy as np
import matplotlib.pyplot as plt


def _new_axes(height=4.5):
    _, ax = plt.subplots(figsize=(10, height), constrained_layout=True)
    return ax


def _clickable_legend(ax, **legend_kwargs):
    """Draws the legend and makes each entry a toggle for its line.

    Clicking the swatch or the label hides that series and greys the entry
    out; clicking again brings it back.
    """

    artists, _ = ax.get_legend_handles_labels()
    legend = ax.legend(**legend_kwargs)

    # legend entries are copies, so map each one back to the real artist
    toggles = {}
    for handle, text, artist in zip(legend.legend_handles, legend.get_texts(), artists):
        for clickable in (handle, text):
            if clickable is not None:
                clickable.set_picker(6)  # 6-pixel click radius
                toggles[clickable] = (artist, handle, text)

    def on_pick(event):
        entry = toggles.get(event.artist)
        if entry is None:
            return
        artist, handle, text = entry

        visible = not artist.get_visible()
        artist.set_visible(visible)
        text.set_alpha(1.0 if visible else 0.35)
        if handle is not None:
            handle.set_alpha(1.0 if visible else 0.35)
        ax.figure.canvas.draw_idle()

    ax.figure.canvas.mpl_connect("pick_event", on_pick)

    # students won't find this unless we tell them it's there
    ax.figure.text(0.995, 0.005, "click legend entries to show/hide lines",
                   ha="right", va="bottom", fontsize=7, color="gray", alpha=0.8)

    # keep a reference so the handler isn't garbage collected
    ax.figure._legend_toggles = toggles
    return legend


def _plot_power(simulator):
    ax = _new_axes()

    ax.plot(simulator.time_steps, simulator.n_current_values,
            label="True neutron population", color="black")
    ax.scatter(simulator.time_steps, simulator.n_measured_values,
               label="Raw noisy reading", color="gray", s=6, alpha=0.4)
    ax.plot(simulator.time_steps, simulator.n_estimated_values,
            label="EKF estimate", color="tab:blue")
    ax.plot(simulator.time_steps, simulator.n_desired_values, "--",
            label="Desired neutron population")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Normalized power")
    ax.set_title("Closed-Loop Reactor Power: true vs. measured vs. filtered")
    _clickable_legend(ax, loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_rod_command(simulator):
    ax = _new_axes()

    # These two only differ when the safety supervisor overrides the
    # controller, or an actuator fault is in play.
    ax.plot(simulator.control_times, simulator.commanded_rho_values,
            label="Controller-commanded rho", color="tab:red",
            linestyle="--", alpha=0.7)
    ax.plot(simulator.control_times, simulator.control_values,
            label="Actually-applied rho", color="orange")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Reactivity, rho (dk/k)")
    ax.set_title("Control-Rod Command: controller request vs. what was actually applied")
    _clickable_legend(ax, loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_thermal_feedback(simulator):
    ax = _new_axes()

    ax.plot(simulator.time_steps, simulator.feedback_rho_values,
            label="Thermal reactivity", color="green")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Reactivity, rho (dk/k)")
    ax.set_title("Thermal Reactivity Feedback")
    _clickable_legend(ax, loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_estimation_error(simulator):
    ax = _new_axes()

    truth = np.array(simulator.n_current_values)
    measured_err = np.abs(np.array(simulator.n_measured_values) - truth)
    estimated_err = np.abs(np.array(simulator.n_estimated_values) - truth)

    ax.plot(simulator.time_steps, measured_err, label="Raw measurement error", color="gray")
    ax.plot(simulator.time_steps, estimated_err, label="EKF estimate error", color="tab:blue")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("|error|")
    ax.set_title("Power Estimation Error: raw vs. filtered")
    _clickable_legend(ax, loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid()


def _plot_safety_state(simulator):
    ax = _new_axes(height=3.5)

    levels = {"NORMAL": 0, "WARNING": 1, "LIMITING": 2, "SCRAM": 3, "SHUTDOWN": 4}
    ax.step(simulator.control_times, [levels[s] for s in simulator.safety_states],
            where="post", color="crimson")

    ax.set_yticks(list(levels.values()), list(levels.keys()))
    ax.set_ylim(-0.5, 4.5)
    ax.set_xlabel("Time (s)")
    ax.set_title("Safety Supervisor State")
    ax.grid()


def _plot_temperatures(simulator):
    ax = _new_axes()

    ax.plot(simulator.time_steps, simulator.fuel_temp_values,
            label="Fuel temp (K)", color="firebrick")
    ax.plot(simulator.time_steps, simulator.coolant_temp_avg_values,
            label="Coolant temp avg (K)", color="teal")
    ax.axhline(simulator.safety.limits["fuel_temp"]["scram"], color="firebrick",
               linestyle=":", alpha=0.6, label="Fuel SCRAM limit")
    ax.axhline(simulator.safety.limits["coolant_temp"]["scram"], color="teal",
               linestyle=":", alpha=0.6, label="Coolant SCRAM limit")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (K)")
    ax.set_title("True Temperatures vs. Safety Limits")
    _clickable_legend(ax, fontsize=8, framealpha=0.9)
    ax.grid()


def plot_simulation(simulator):
    """Opens every diagnostic view for a finished run."""

    _plot_power(simulator)
    _plot_rod_command(simulator)
    _plot_thermal_feedback(simulator)
    _plot_estimation_error(simulator)
    _plot_safety_state(simulator)
    _plot_temperatures(simulator)
    plt.show()
