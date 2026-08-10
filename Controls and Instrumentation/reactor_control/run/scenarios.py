"""Named test scenarios for the reactor controller (Milestone 5: disturbances
and faults). Each scenario configures a fresh Simulation/Controller/
SensorSuite and, where relevant, a sensor or actuator fault."""

from run.simulation import Simulation
from controller.control import CONTROLLERS
from reactor.sensors import SensorSuite

SCENARIOS = {
    "nominal": {
        # Genuinely undisturbed -- the reference case to compare the others
        # against. The model defaults to a small reactivity bump at t=50-100,
        # so this explicitly switches it off.
        "desired_n": 1.0,
        "disturbance_magnitude": 0.0,
    },
    "load_step": {
        # Controller must track a new setpoint instead of holding steady.
        #
        # 1.5% and no higher: the rods are worth +/-5e-4 reactivity, and the
        # thermal feedback eats 2.475e-2 of reactivity per unit of power, so
        # fully withdrawn only sustains about n = 1.020. Ask for more than
        # that and the rod just pins at its limit and never gets there.
        "desired_n": 1.015,
    },
    "coolant_disturbance": {
        # Bigger and longer than the model's default disturbance -- pushes
        # the supervisor into WARNING/LIMITING, then recovers on its own
        # without a SCRAM. Milestone 5's "recover from a disturbance
        # without unsafe excursions" demo.
        "desired_n": 1.0,
        "disturbance_magnitude": 0.0006,
        "disturbance_start": 50.0,
        "disturbance_end": 120.0,
    },
    "severe_transient": {
        # Deliberately large enough to blow through the LIMITING margin --
        # demonstrates the safety supervisor actually SCRAMming and
        # latching. Milestone 3's demo.
        "desired_n": 1.0,
        "disturbance_magnitude": 0.0012,
        "disturbance_start": 50.0,
        "disturbance_end": 120.0,
    },
    "sensor_bias": {
        # Drift rate chosen so the accumulated bias clears the fault
        # monitor's threshold (~4 sigma on a sigma=0.005 sensor, i.e. ~0.02)
        # partway through the run, instead of staying lost in the noise.
        "desired_n": 1.0,
        "sensor_fault": {"sensor": "power", "type": "drift", "params": {"drift_rate": 3e-4}},
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


def build_simulation(name, duration=200.0, dt=0.1, controller_name="pid"):
    """Builds (simulator, controller, sensor_suite, actuator_fault) for the
    named scenario, ready to pass to Simulation.simulate()."""

    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'. Options: {sorted(SCENARIOS)}")

    if controller_name not in CONTROLLERS:
        raise ValueError(
            f"Unknown controller '{controller_name}'. Options: {sorted(CONTROLLERS)}. "
            "Add your own to CONTROLLERS in control.py."
        )

    cfg = SCENARIOS[name]

    simulator = Simulation(duration=duration, dt=dt, desired_n=cfg.get("desired_n", 1.0))

    if "disturbance_magnitude" in cfg:
        simulator.model.disturbance_magnitude = cfg["disturbance_magnitude"]
    if "disturbance_start" in cfg:
        simulator.model.disturbance_start = cfg["disturbance_start"]
    if "disturbance_end" in cfg:
        simulator.model.disturbance_end = cfg["disturbance_end"]

    controller = CONTROLLERS[controller_name]()
    sensor_suite = SensorSuite()

    if "sensor_fault" in cfg:
        fault = cfg["sensor_fault"]
        getattr(sensor_suite, fault["sensor"]).set_fault(fault["type"], fault.get("params"))

    actuator_fault = cfg.get("actuator_fault")

    return simulator, controller, sensor_suite, actuator_fault
