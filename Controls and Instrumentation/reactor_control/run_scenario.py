import argparse

from controller.control import CONTROLLERS
from run.scenarios import SCENARIOS, build_simulation


def positive_float(value):
    """Parse a positive finite command-line number."""

    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc

    if number <= 0 or number == float("inf") or number != number:
        raise argparse.ArgumentTypeError("must be positive and finite")
    return number


def non_negative_int(value):
    """Parse a non-negative command-line integer."""

    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if number < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return number


def main():
    parser = argparse.ArgumentParser(
        description="Run a named reactor control scenario."
    )
    parser.add_argument(
        "--scenario", choices=sorted(SCENARIOS), default="nominal"
    )
    parser.add_argument(
        "--controller",
        choices=sorted(CONTROLLERS),
        default="pid",
        help="Controller to run. Register new controllers in control.py.",
    )
    parser.add_argument("--duration", type=positive_float, default=200.0)
    parser.add_argument(
        "--seed",
        type=non_negative_int,
        default=0,
        help="Sensor-noise seed. Reuse it for fair controller comparisons.",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Feed raw power readings to the controller instead of the EKF estimate.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip plot windows for headless runs.",
    )
    args = parser.parse_args()

    simulator, controller, sensor_suite, actuator_fault = build_simulation(
        args.scenario,
        duration=args.duration,
        controller_name=args.controller,
        seed=args.seed,
    )
    simulator.simulate(
        controller,
        sensor_suite,
        use_filter=not args.no_filter,
        actuator_fault=actuator_fault,
    )

    time_by_state = {
        state: sum(
            step_duration
            for observed, step_duration in zip(
                simulator.safety_states, simulator.control_durations
            )
            if observed == state
        )
        for state in ("WARNING", "LIMITING", "SCRAM", "SHUTDOWN")
    }
    scram_time = time_by_state["SCRAM"] + time_by_state["SHUTDOWN"]

    print(f"Scenario: {args.scenario}  (controller: {args.controller})")
    print(f"Final safety state: {simulator.safety_states[-1]}")
    print(f"Time in WARNING:  {time_by_state['WARNING']:.2f} s")
    print(f"Time in LIMITING: {time_by_state['LIMITING']:.2f} s")
    print(f"Time in SCRAM/SHUTDOWN: {scram_time:.2f} s")

    if not args.no_plot:
        simulator.plot()


if __name__ == "__main__":
    main()
