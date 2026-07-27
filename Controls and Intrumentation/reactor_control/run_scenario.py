import argparse

from scenarios import build_simulation, SCENARIOS


def main():
    parser = argparse.ArgumentParser(description="Run a named reactor control scenario.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="nominal")
    parser.add_argument("--duration", type=float, default=200.0)
    parser.add_argument("--no-filter", action="store_true", help="Feed the controller raw sensor readings instead of the EKF estimate.")
    parser.add_argument("--no-plot", action="store_true", help="Skip showing the plot (useful for headless runs).")
    args = parser.parse_args()

    simulator, controller, sensor_suite, actuator_fault = build_simulation(
        args.scenario, duration=args.duration
    )
    simulator.simulate(
        controller, sensor_suite,
        use_filter=not args.no_filter,
        actuator_fault=actuator_fault,
    )

    scram_steps = sum(1 for s in simulator.safety_states if s in ("SCRAM", "SHUTDOWN"))
    limiting_steps = sum(1 for s in simulator.safety_states if s == "LIMITING")
    warning_steps = sum(1 for s in simulator.safety_states if s == "WARNING")
    total_steps = len(simulator.safety_states)

    print(f"Scenario: {args.scenario}")
    print(f"Final safety state: {simulator.safety_states[-1]}")
    print(f"Steps in WARNING:  {warning_steps} / {total_steps}")
    print(f"Steps in LIMITING: {limiting_steps} / {total_steps}")
    print(f"Steps in SCRAM/SHUTDOWN: {scram_steps} / {total_steps}")

    final_flags = simulator.fault_flag_history[-1] if simulator.fault_flag_history else {}
    flagged_channels = [name for name, flagged in final_flags.items() if flagged]
    if flagged_channels:
        for name in flagged_channels:
            first_t = next(
                simulator.control_times[i]
                for i, flags in enumerate(simulator.fault_flag_history)
                if flags.get(name)
            )
            print(f"Suspected sensor fault: '{name}' flagged at t={first_t:.1f}s")
    else:
        print("No sensor faults flagged.")

    if any(simulator.disturbance_suspected_history):
        first_t = simulator.control_times[simulator.disturbance_suspected_history.index(True)]
        print(f"Multiple channels disagreed with the model at once starting t={first_t:.1f}s "
              f"-- looks like an unmodeled disturbance, not a single sensor fault.")

    if not args.no_plot:
        simulator.plot()


if __name__ == "__main__":
    main()
