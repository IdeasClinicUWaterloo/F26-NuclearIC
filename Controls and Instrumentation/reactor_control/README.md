# Simulated Reactor Track

This is the simulated reactor option for the [Controls and Instrumentation challenge](../README.md). It includes a reactor model, controller, noisy sensors, EKF state estimator, safety logic and fault scenarios.

## Table of Contents

- [Setup](#setup)
- [Project files](#project-files)
- [Run a scenario](#run-a-scenario)
- [Write a controller](#write-a-controller)
- [Known gaps](#known-gaps)
- [Suggested workflow](#suggested-workflow)
- [Resources](#resources)

## Setup

Run these commands from the `reactor_control` folder.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Project files

| File | Purpose |
| --- | --- |
| `run_scenario.py` | Command-line entry point |
| `controller/control.py` | PID controller and controller registry |
| `controller/state_machine.py` | Warning, limiting, SCRAM and shutdown logic |
| `reactor/model.py` | Point-kinetics and thermal reactor model |
| `reactor/sensors.py` | Noisy sensors and fault injection |
| `estimation/ekf.py` | Extended Kalman filter |
| `run/simulation.py` | Main simulation loop |
| `run/scenarios.py` | Scenario settings |
| `run/plotting.py` | Result plots |

Start with `controller/control.py`, then run a few scenarios before changing the model.

## Run a scenario

```bash
python run_scenario.py --scenario nominal
```

Full command:

```bash
python run_scenario.py --scenario <name> [--controller pid] [--duration 200] [--seed 0] [--no-filter] [--no-plot]
```

| Option | Purpose |
| --- | --- |
| `--controller` | Selects a registered controller |
| `--duration` | Sets the simulation time |
| `--seed` | Repeats the same sensor noise |
| `--no-filter` | Sends raw readings to the controller instead of EKF estimates |
| `--no-plot` | Runs without opening plots |

Reuse the same seed when comparing controllers.

### Scenarios

| Scenario | Test |
| --- | --- |
| `nominal` | Normal operation |
| `load_step` | Power setpoint change |
| `coolant_disturbance` | Recoverable coolant transient |
| `severe_transient` | SCRAM and shutdown response |
| `sensor_bias` | Drifting power sensor |
| `sensor_dropout` | Missing fuel-temperature reading |
| `stuck_rod` | Stuck rod actuator |
| `delayed_rod` | Delayed rod response |

The output reports the final safety state and time spent in each state. Plot legends can be clicked to hide or show lines.

## Write a controller

Create a class with an `update()` method:

```python
class MyController:
    def update(self, desired_n, current_n, dt):
        return rod_speed
```

Inputs:

- `desired_n` is the normalized power setpoint
- `current_n` is measured or filtered power
- `dt` is the time step in seconds

The return value is rod speed in reactivity per second. `run/simulation.py` integrates it into rod position and applies actuator limits.

Register the controller in `controller/control.py`:

```python
CONTROLLERS = {
    "pid": lambda: Controller(kp=3e-4, ki=0, kd=0),
    "mine": lambda: MyController(),
}
```

Run it with:

```bash
python run_scenario.py --scenario load_step --controller mine
```

The safety supervisor, actuator faults and plots work with any registered controller.

## Known gaps

- There is no fault-diagnosis module
- The two coolant sensors are not used for voting
- `rod_reactivity` is measured but unused
- Rod authority limits power changes to about ±2%
- The default PID uses proportional control only
- There is no automatic scoring tool for controller comparisons

These gaps are possible project directions.

## Suggested workflow

1. Run `nominal` and understand the plots.
2. Run `load_step` and tune the controller.
3. Run `coolant_disturbance` and `severe_transient` to test safety logic.
4. Compare normal runs with and without `--no-filter`.
5. Run the four sensor and actuator fault scenarios.
6. Improve control, estimation, safety, fault detection, scoring or visualization.

Good results should show setpoint tracking, safe behaviour and recovery from at least one disturbance or fault.

## Resources

- [Point Kinetics Equations](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/point-kinetics-equations/)
- [SMR modeling and control review](https://ieeexplore.ieee.org/document/10384339)
- [Nuclear power plant safety systems](https://www.nrc.gov/reading-rm/basic-ref/students/what-is-nuclear-energy)
- [PID anti-windup](https://www.mathworks.com/videos/understanding-pid-control-part-2-expanding-beyond-a-simple-integral-1528310418260.html)
- [Kalman filter introduction](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/)
- [SciPy `solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
- [Matplotlib documentation](https://matplotlib.org/stable/index.html)
