import argparse

from scenarios import build_simulation, SCENARIOS
from control import CONTROLLERS


def main():
    parser = argparse.ArgumentParser(description="Run a named reactor control scenario.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="nominal")
    parser.add_argument("--controller", choices=sorted(CONTROLLERS), default="pid",
                        help="Which controller to run. Register your own in control.py.")
    parser.add_argument("--duration", type=float, default=200.0)
    parser.add_argument("--no-filter", action="store_true", help="Feed the controller raw sensor readings instead of the EKF estimate.")
    parser.add_argument("--no-plot", action="store_true", help="Skip showing the plot (useful for headless runs).")
    args = parser.parse_args()

    simulator, controller, sensor_suite, actuator_fault = build_simulation(
        args.scenario, duration=args.duration, controller_name=args.controller
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

    print(f"Scenario: {args.scenario}  (controller: {args.controller})")
    print(f"Final safety state: {simulator.safety_states[-1]}")
    print(f"Steps in WARNING:  {warning_steps} / {total_steps}")
    print(f"Steps in LIMITING: {limiting_steps} / {total_steps}")
    print(f"Steps in SCRAM/SHUTDOWN: {scram_steps} / {total_steps}")

    if not args.no_plot:
        simulator.plot()


if __name__ == "__main__":
    main()
