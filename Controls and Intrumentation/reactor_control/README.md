# Reactor Control: Simulated Reactor Track

This folder is the simulated-reactor half of the Instrumentation and Controls challenge (see the [top-level README](../README.md) for the challenge overview). Unlike a blank scaffold, the code here is a working reference implementation: a point-kinetics + thermal reactor model, a PID controller, an EKF state estimator, and a latching safety state machine, wired together through a set of named test scenarios.

Use it to understand how the pieces fit together, then replace or extend whichever piece your team wants to make its own. It is a reference, not a finished product. Some things are deliberately left undone (see [Known Gaps](#known-gaps)), and fault diagnosis is missing entirely.

For a simpler, earlier exploration of the same model (PID + a basic Kalman filter, no safety supervisor), see `../reactor_ctrl_aahan/`. That one is not the maintained package and is missing several pieces described below, so build on this folder instead.

---

## Table of Contents

- [Roadmap](#roadmap)
- [Files](#files)
- [Setup](#setup)
- [Running a Scenario](#running-a-scenario)
- [Writing Your Own Controller](#writing-your-own-controller)
- [Known Gaps](#known-gaps)
- [How Real Reactors Do This](#how-real-reactors-do-this)
- [Resources](#resources)

---

## Roadmap

These milestones describe what already works in this folder and what to verify or build on next. They are guides, not a scoring checklist. If you have not run anything yet, do [Setup](#setup) first.

### Milestone 1: Run the Reactor Simulation

- Read the [point kinetics equations](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/point-kinetics-equations/), then read `model.py`'s `neutron_equations` and `thermal_equations`.
- Run `python run_scenario.py --scenario nominal` and inspect the plots.
- Identify the control input (`Controller.update` returns a rod speed), the sensor outputs (`SensorSuite`'s five channels), and the hidden values the sensors never see: the six precursor concentrations `C1` to `C6` and the two coolant-node temperatures.

Good demo: explain how the model responds when `rho_rod` changes, and why the six precursor groups matter for how fast power can change.

### Milestone 2: Build a Basic Power Controller

- `control.py` implements an anti-windup PID on rod speed. It currently runs as P-only with `kp=3e-4`.
- Run `--scenario load_step` and observe tracking, overshoot, and settling time. It reaches the setpoint to within about 0.07% in roughly 190 s.
- Try adding `ki`/`kd` and compare. See [how to tune a PID controller](https://www.digikey.com/en/maker/projects/how-to-tune-a-pid-controller/9ee9a111aef049af9f84f785779989ec).
- Turn `kp` up and watch the trade-off. Tracking gets faster, but past about `1e-3` the rods spend most of their time pegged at maximum speed chasing sensor noise. That is a real failure mode, not a simulation artefact.

Good demo: the controller tracks a setpoint change without immediately violating safety limits.

### Milestone 3: Add Safety Logic

- `state_machine.py`'s `SafetySupervisor` already implements the warn/limit/scram thresholds and the rod override, including the SCRAM latch.
- Run `--scenario severe_transient` to see the supervisor actually SCRAM and hold `SHUTDOWN`.
- Run `--scenario coolant_disturbance` to see it recover through WARNING/LIMITING without ever SCRAMming.

Good demo: explain why SCRAM latches instead of clearing itself once conditions look normal again, and what `scram_rho` represents physically.

### Milestone 4: Improve Instrumentation and State Estimation

- `ekf.py` estimates all ten reactor values, including the precursors and coolant nodes nothing measures, from four noisy sensors: power and the three temperatures. Start with [How a Kalman Filter Works, in Pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/) if the maths is unfamiliar.
- Compare a run with and without `--no-filter`, and check the estimation-error figure (true vs. measured vs. estimated).
- `Q` in `simulation._build_ekf` is the main lever on how well the estimate tracks. Try changing it and watch what happens.

Good demo: the controller performs better using the EKF estimate than raw noisy measurements alone.

### Milestone 5: Handle Disturbances and Faults

- Run each of `sensor_bias`, `sensor_dropout`, `stuck_rod`, and `delayed_rod` and watch what the controller does. It survives all four, but not always gracefully. In `sensor_bias` it ends up confidently holding the wrong power.
- **Detection is entirely up to you.** There is no fault-detection code in the starter. Getting the system to notice something is wrong, say which channel, and do something sensible about it is the substance of this milestone. See [Known Gaps](#known-gaps) for what makes it harder than it first looks.

Good demo: the controller rides out at least one fault without an unsafe excursion. If you build detection, it names the channel that is actually broken rather than one that merely looks broken.

### Milestone 6: Make Your Solution Unique

Possible directions, once you understand the baseline above:

- Better control: PID tuning, gain scheduling, LQR, or MPC in `control.py`
- Better estimation: sensor fusion or bias estimation in `ekf.py`
- Better safety: more robust SCRAM logic or safety margins in `state_machine.py`
- Better diagnostics: fault detection and isolation from scratch, since there is nothing there to start from
- Better visualization: a live dashboard instead of `plotting.py`'s static figures, or scenario comparison plots
- Better evaluation: an automated sweep across all `SCENARIOS` with a score breakdown

Good demo: a clear idea beyond the baseline, and why it improves control, safety, estimation, or interpretability.

---

## Files

Tagged by how much background you need. **Start here** and **Easy** are good first-day targets. **Advanced** files are worth reading, but you can treat them as working black boxes and still build a strong project.

| Level | File | What's in it |
| --- | --- | --- |
| **Start here** | `control.py` | `Controller`: PID on power error, with anti-windup. Outputs a rod *speed*, which `simulation.py` turns into a rod position. Tuning `kp`/`ki`/`kd`, or replacing this class entirely, is the most direct way to change how the reactor behaves. |
| **Easy** | `scenarios.py` | Named scenario configs and `build_simulation()`. Adding your own scenario is a few lines of dict. |
| **Easy** | `plotting.py` | `plot_simulation()`: power tracking, rod command, thermal feedback, estimation error, safety state, and temperatures against limits, as separate matplotlib figures. |
| **Easy** | `run_scenario.py` | Command-line entry point. |
| **Moderate** | `state_machine.py` | `SafetySupervisor`: NORMAL, WARNING, LIMITING, SCRAM, SHUTDOWN. It reads the raw sensors rather than the EKF, and latches once SCRAMmed. Plain threshold logic, readable without a controls background, and the thresholds are yours to argue with. |
| **Moderate** | `sensors.py` | `Sensor` (noise + bias, with `drift` / `stuck` / `dropout` faults you can inject) and `SensorSuite` (power, fuel_temp, coolant_temp_1, coolant_temp_2, rod_reactivity). Note `rod_reactivity` is simulated but nothing currently uses it. |
| **Moderate** | `simulation.py` | `Simulation`: the run loop that ties model, controller, sensors, EKF, and safety supervisor together. Read `simulate()` to see the order things happen in. Also runnable on its own with `python simulation.py`. |
| **Advanced** | `model.py` | `ReactorModel`: six-group delayed-neutron point kinetics coupled to a three-node thermal model (fuel, coolant node 1, coolant node 2), with temperature feedback and an optional timed disturbance. This is the reactor itself, so you generally want to control it rather than change it. |
| **Advanced** | `ekf.py` | `EKF`: an extended Kalman filter that estimates all ten reactor values from four sensors. Also exposes `normalized_innovation()`, which nothing currently uses. It is there as a starting point for fault detection. |

There is deliberately **no fault-detection module**. The scenarios break things, but nothing notices. That is one of the open problems (see [Known Gaps](#known-gaps)).

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
```

---

## Running a Scenario

```bash
python run_scenario.py --scenario <name> [--controller pid] [--duration 200] [--no-filter] [--no-plot]
```

- `--controller` picks which controller to run (see [Writing Your Own Controller](#writing-your-own-controller)).
- `--no-filter` feeds the controller raw sensor readings instead of the EKF estimate. A direct way to show what your estimator is buying you.
- `--no-plot` skips the plot windows (useful for headless runs).
- Output includes the final safety state and the time spent in each safety state.

**Click any legend entry to show or hide that line.** The raw-sensor cloud in particular buries everything else. Hide it and the true power, the estimate, and the setpoint become readable.

Available `--scenario` values:

| Scenario | What it exercises |
| --- | --- |
| `nominal` | Undisturbed baseline, the reference case to compare everything else against. |
| `load_step` | Controller must track a new power setpoint, up 1.5%. Not larger, because that is close to all the rods can sustain (see [Known Gaps](#known-gaps)). |
| `coolant_disturbance` | A disturbance big enough to push WARNING/LIMITING, then recover without a SCRAM. |
| `severe_transient` | A disturbance big enough to blow through the LIMITING margin, so the safety supervisor actually SCRAMs and latches. |
| `sensor_bias` | The power sensor slowly drifts off true, so the controller is confidently holding the wrong power. |
| `sensor_dropout` | The fuel temperature sensor goes dead and reads NaN. The EKF carries on using the three sensors still working, which is a good illustration of why you use several rather than trusting one. |
| `stuck_rod` | The control rod sticks in place partway through the run. |
| `delayed_rod` | The control rod responds late, working through old commands. |

---

## Writing Your Own Controller

The PID is deliberately easy to replace. Write a class with a single `update()` method:

```python
class MyController:
    def update(self, desired_n, current_n, dt):
        # desired_n : the power we want, where 1.0 is full rated power
        # current_n : the power we have right now
        #             (filtered by the EKF, unless you pass --no-filter)
        # dt        : seconds since this was last called
        return speed   # how fast to move the rods, in reactivity per second
```

You say how fast to **move** the rods, not where to put them. That is how a real
plant does it (see [How Real Reactors Do This](#how-real-reactors-do-this)).
`simulation.py` adds your speed up over time into a position and caps it at the
motor's top speed, so the rods cannot jump instantly however large a number you
return.

One useful side effect: the rods keep creeping for as long as you ask for any
speed at all, so they carry on until the error is gone. Even with just the P
term switched on, you end up with no leftover offset.

Register it at the bottom of `control.py`:

```python
CONTROLLERS = {
    "pid": lambda: Controller(kp=3e-4, ki=0, kd=0),
    "mine": lambda: MyController(),
}
```

Then run it:

```bash
python run_scenario.py --scenario load_step --controller mine
```

Everything downstream keeps working with whatever you return: the safety
supervisor, the actuator faults, and all the plots. So you can compare your
controller against the PID on the same scenarios without touching anything else.

---

## Known Gaps

Things the starter does not do, left open on purpose. Any of them is a fair target.

- **Nothing detects faults.** The scenarios break sensors and rods, but no code notices. Two things we found when we tried: the EKF quietly absorbs a slow drift, so the numbers it reports stay small even while the sensor goes badly wrong; and one broken sensor drags the others off too, so the channel that looks worst is often not the broken one. `EKF.normalized_innovation()` is a reasonable place to start, but a check that ignores the filter completely might work better.

- **Two coolant sensors, never compared.** `coolant_temp_1` and `coolant_temp_2` measure almost the same thing, so if they disagree, one is probably broken. Real plants use exactly this trick. The catch: during a severe transient they genuinely differ by up to about 20 K, because node 2 lags behind node 1, so a simple "are they far apart" test raises false alarms.

- **`rod_reactivity` is measured and then ignored.** Nothing reads it. It could spot a stuck or slow rod directly, instead of guessing from how the power responds.

- **The rods can only shift power by about 2%.** Push them all the way out and power settles around 1.020, no higher. That is why `load_step` only asks for 1.015. Real plants get around this by dissolving boron in the coolant for the big changes and keeping the rods for fine adjustments. Adding something like that, or simply making the rods stronger, is a fair change to make.

- **The PID only uses the P term** (`ki=0, kd=0`). Less broken than it sounds, since the rods keep moving until the error is gone, but the transient still has plenty of room in it.

- **No way to score a run.** There is no automatic way to try every scenario and compare two controllers by the numbers. Building one makes every other change easier to justify.

---

## How Real Reactors Do This

Worth knowing where the starter is faithful and where it simplifies. The
description below follows Wang et al., *[Small Modular Reactors: An Overview of
Modeling, Control, Simulation, and Applications](https://ieeexplore.ieee.org/document/10384339)*,
IEEE Access 2024. Section II.C covers light water reactor control.

**What we model the same way:**

- **Rod speed, not rod position.** A real plant feeds a *rod velocity control unit* that sets "control rod movement speed and direction". That is exactly what `Controller.update()` returns.
- **Temperature pushes back on power.** The paper is explicit that cores are designed so rising temperature *reduces* reactivity, because the opposite runs away. Our `alpha_fuel` and `alpha_cool` are both negative for this reason.
- **Filtering to stop the rods hunting.** Real designs include a filter to "eliminate small and abrupt disturbance signals, preventing frequent movement of control rods". Feeding the controller the EKF estimate rather than the raw reading does the same job here.

**What we simplify:**

- **We control power; real PWRs control coolant temperature.** The usual schemes hold steam pressure, average coolant temperature, or coolant outlet temperature steady. Power is what sets the *target* temperature, not the thing being regulated. Pointing this controller at coolant temperature instead, with a target worked out from the requested power, would be a genuinely realistic upgrade.
- **Real control uses three signals, not one.** A PWR combines a temperature reading (corrected for how slowly the thermometer responds), a target temperature, and a power-mismatch signal that acts when power has moved but temperature has not caught up yet. We only have the equivalent of the third.
- **No boron.** A real PWR dissolves boron in the coolant to handle the big, slow reactivity changes, leaving the rods mostly withdrawn during normal running. Our single rod does everything, which is why it runs out of authority so quickly.

---

## Resources

### Background Information

- [Point Kinetics Equations](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/point-kinetics-equations/): the neutron-population model `model.py` implements, including why delayed neutrons are what make a reactor controllable at all.
- [Reactor Dynamics](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/): broader context on reactivity, feedback, and transients.

### Technical Resources

- [How a Kalman Filter Works, in Pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/): the clearest visual introduction to Kalman filtering. Read this before `ekf.py`. It explains the predict/update cycle and what the uncertainty matrices are actually doing.
- [How to Tune a PID Controller](https://www.digikey.com/en/maker/projects/how-to-tune-a-pid-controller/9ee9a111aef049af9f84f785779989ec): practical tuning procedure for the `kp`/`ki`/`kd` gains in `control.py`.
- [SciPy `solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html): the ODE solver the model uses. The reactor has both very fast and very slow parts, which is why it runs the `Radau` method rather than the default.
- [Matplotlib documentation](https://matplotlib.org/stable/index.html): for extending `plotting.py`.

### Additional References

- [Integral windup](https://en.wikipedia.org/wiki/Integral_windup): why `control.py` stops adding to its running total once the rod motor is flat out.
- [Extended Kalman Filter](https://en.wikipedia.org/wiki/Extended_Kalman_filter): the version used here, for systems that are not straight lines.
- [Fault detection and isolation](https://en.wikipedia.org/wiki/Fault_detection_and_isolation): background for the detection work left open in [Known Gaps](#known-gaps).
