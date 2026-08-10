"""Named reactor-control scenarios and their fault configuration."""

from run.simulation import Simulation
from controller.control import CONTROLLERS
from reactor.sensors import SensorSuite

SCENARIOS = {
    "nominal": {
        # Disable the model's default disturbance for a clean reference run.
        "desired_n": 1.0,
        "disturbance_magnitude": 0.0,
    },
    "load_step": {
        # The rods can sustain about +2% power, so this step stays reachable.
        "desired_n": 1.015,
    },
    "coolant_disturbance": {
        # Crosses WARNING/LIMITING, then recovers without a SCRAM.
        "desired_n": 1.0,
        "disturbance_magnitude": 0.0006,
        "disturbance_start": 50.0,
        "disturbance_end": 120.0,
    },
    "severe_transient": {
        # Crosses the SCRAM threshold and exercises the latch.
        "desired_n": 1.0,
        "disturbance_magnitude": 0.0012,
        "disturbance_start": 50.0,
        "disturbance_end": 120.0,
    },
    "sensor_bias": {
        # Reaches a visible +6% bias over the default 200-second run.
        "desired_n": 1.0,
        "sensor_fault": {
            "sensor": "power",
            "type": "drift",
            "params": {"drift_rate": 3e-4},
        },
    },
    "sensor_dropout": {
        "desired_n": 1.0,
        "sensor_fault": {"sensor": "fuel_temp", "type": "dropout"},
    },
    "stuck_rod": {
        "desired_n": 1.0,
        "actuator_fault": {"type": "stuck", "t_start": 60.0},
    },
    "delayed_rod": {
        "desired_n": 1.0,
        "actuator_fault": {"type": "delay", "t_start": 0.0, "lag_steps": 15},
    },
}


def build_simulation(name, duration=200.0, dt=0.1, controller_name="pid",
                     seed=0):
    """Return a fresh simulation, controller, sensors, and actuator fault."""

    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'. Options: {sorted(SCENARIOS)}")

    if controller_name not in CONTROLLERS:
        raise ValueError(
            f"Unknown controller '{controller_name}'. Options: {sorted(CONTROLLERS)}. "
            "Add your own to CONTROLLERS in control.py."
        )

    cfg = SCENARIOS[name]

    simulator = Simulation(
        duration=duration,
        dt=dt,
        desired_n=cfg.get("desired_n", 1.0),
    )

    if "disturbance_magnitude" in cfg:
        simulator.model.disturbance_magnitude = cfg["disturbance_magnitude"]
    if "disturbance_start" in cfg:
        simulator.model.disturbance_start = cfg["disturbance_start"]
    if "disturbance_end" in cfg:
        simulator.model.disturbance_end = cfg["disturbance_end"]

    controller = CONTROLLERS[controller_name]()
    sensor_suite = SensorSuite(seed=seed)

    if "sensor_fault" in cfg:
        fault = cfg["sensor_fault"]
        sensor = getattr(sensor_suite, fault["sensor"], None)
        if sensor is None:
            raise ValueError(
                f"Unknown sensor in scenario {name!r}: {fault['sensor']!r}"
            )
        sensor.set_fault(fault["type"], fault.get("params"))

    actuator_fault = cfg.get("actuator_fault")

    return simulator, controller, sensor_suite, actuator_fault
