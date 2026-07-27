# Simulated Reactor Track

This folder is the simulated-reactor half of the Instrumentation and Controls challenge (see the [top-level README](../README.md) for the challenge overview). The code here is a working reference implementation: a point-kinetics + thermal reactor model, a PID controller, an EKF state estimator, and a latching safety state machine, wired together through a set of named test scenarios.

Use it to understand how the pieces fit together, then replace or extend whichever piece your team wants to make its own. It is a reference, not a finished product, some things are deliberately left undone (see [Known Gaps](#known-gaps)), and fault diagnosis is missing entirely.

---

## Table of Contents

- [Files](#files)
- [Setup](#setup)
- [Running a Scenario](#running-a-scenario)
- [Writing Your Own Controller](#writing-your-own-controller)
- [Known Gaps](#known-gaps)
- [How Real Reactors Do This](#how-real-reactors-do-this)
- [Roadmap](#roadmap)
- [Resources](#resources)
---

## Files

Tagged by how much background you need. **Start here** and **Easy** are good first-day targets; **Advanced** files are worth reading but you can treat them as working black boxes and still build a strong project.

Make sure to run the project multiple times first with different scenarios, and understand how it works.

The code is split into four folders by what each part is responsible for:

```
reactor_control/
  run_scenario.py       run this
  controller/           your job: decide how to move the rods
    control.py
    state_machine.py
  reactor/              the simulated plant and its instruments
    model.py
    sensors.py
  estimation/           turning noisy readings into usable numbers
    ekf.py
  run/                  the machinery that runs, configures, and draws it
    simulation.py
    scenarios.py
    plotting.py
```

Everything imports through those folder names, for example
`from controller.control import Controller`. Run commands from the
`reactor_control` folder so Python can find them.

| Level | File | What's in it |
| --- | --- | --- |
| **Start here** | `controller/control.py` | `Controller`: PID on neutron-population error, with anti-windup. Outputs a rod *speed*, which `run/simulation.py` integrates into a rod position. Tuning `kp`/`ki`/`kd`, or replacing this class entirely, is the most direct way to change how the reactor behaves. |
| **Easy** | `run/scenarios.py` | Named scenario configs and `build_simulation()`. Adding your own scenario is a few lines of dict. |
| **Easy** | `run/plotting.py` | `plot_simulation()`: power tracking, rod command, thermal feedback, estimation error, safety state, and temperatures-vs-limits, as separate matplotlib figures. |
| **Easy** | `run_scenario.py` | CLI entry point. |
| **Moderate** | `controller/state_machine.py` | `SafetySupervisor`: NORMAL → WARNING → LIMITING → SCRAM → SHUTDOWN, evaluated from raw (unfiltered) instrumentation independently of the EKF, and latches once SCRAMmed.
| **Moderate** | `reactor/sensors.py` | `Sensor` (Gaussian noise + bias, with `drift` / `stuck` / `dropout` fault injection) and `SensorSuite` (power, fuel_temp, coolant_temp_1, coolant_temp_2, rod_reactivity). Note `rod_reactivity` is simulated but nothing currently uses it. |
| **Moderate** | `run/simulation.py` | `Simulation`: the per-timestep run loop tying model + controller + sensors + EKF + safety supervisor together. Read `simulate()` to see the order things happen in. Also runnable on its own with `python -m run.simulation`. |
| **Advanced** | `reactor/model.py` | `ReactorModel`: 6-group delayed-neutron point kinetics coupled to a 3-node thermal model (fuel, coolant node 1, coolant node 2), with fuel/coolant reactivity feedback and an optional timed external disturbance. This is the reactor itself. You generally want to leave it alone and control it, not change it. |
| **Advanced** | `estimation/ekf.py` | `EKF`: extended Kalman filter using a numerical Jacobian and matrix-exponential discretization for the stiff neutron mode. Also exposes `normalized_innovation()`, which nothing currently uses, it's there as a starting point for fault detection. |

There is deliberately **no fault-detection module**. The scenarios inject faults, but nothing diagnoses them. That's one of the open problems (see [Known Gaps](#known-gaps)).

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
- `--no-filter` feeds the controller raw sensor readings instead of the EKF estimate: a direct way to show what your estimator is buying you.
- `--no-plot` skips the plot windows.
- Output includes the final safety state and the time spent in each safety state.

**Click any legend entry to show or hide that line.**

Available `--scenario` values:

| Scenario | What it exercises |
| --- | --- |
| `nominal` | Undisturbed baseline. The reference case to compare everything else against. |
| `load_step` | Controller must track a new power setpoint (+1.5%). Not larger, because that is close to all the rods can sustain: see [Known Gaps](#known-gaps). |
| `coolant_disturbance` | A disturbance large enough to push WARNING/LIMITING, then recover without a SCRAM. |
| `severe_transient` | A disturbance large enough to blow through the LIMITING margin: the safety supervisor actually SCRAMs and latches. |
| `sensor_bias` | The power sensor slowly drifts off true, so the controller is confidently regulating a lie. |
| `sensor_dropout` | The fuel temperature sensor goes dead (reads NaN). The EKF keeps estimating from the three channels still alive. A good illustration of why you fuse several sensors rather than trusting one. |
| `stuck_rod` | The control rod actuator sticks in place partway through the run. |
| `delayed_rod` | The control rod actuator responds with a lag. |

---

## Writing Your Own Controller

The PID is deliberately easy to replace. Write a class with a single `update()` method:

```python
class MyController:
    def update(self, desired_n, current_n, dt):
        # desired_n : setpoint, normalized power (1.0 = rated)
        # current_n : power right now, filtered unless --no-filter
        # dt        : seconds since the last call
        return speed   # how fast to drive the rods, in reactivity/second
```

You command a rod **speed**, not a rod position. That's how a real plant does
it (see [How Real Reactors Do This](#how-real-reactors-do-this)). `run/simulation.py`
integrates your speed into a position and enforces the drive motor's maximum,
so you can't teleport the rods however large a number you return.

Because rod position is the integral of your command, note that a plain
proportional controller here already acts like an integrator on position and
will drive steady-state error to zero by itself.

Register it at the bottom of `controller/control.py`:

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

Everything downstream (the safety supervisor, actuator faults, and all the plots) keeps working with whatever you return, so you can compare your controller against the PID on the same scenarios without touching anything else.

---

## Known Gaps

Real limitations of the starter, left open on purpose. Any of these is a legitimate thing to attack.

- **Nothing detects faults.** The scenarios inject sensor drift, dropout, and stuck/lagging rods, but no code notices. Two warnings from having tried: the EKF quietly *absorbs* a slow drift, so its residuals stay small and naive thresholding misses it entirely; and a fault in one channel propagates through the estimator, so the channel that looks worst is often not the broken one. `EKF.normalized_innovation()` is a starting signal, but a check that doesn't depend on the filter at all may work better.
- **The two coolant sensors are redundant but unused.** `coolant_temp_1` and `coolant_temp_2` measure nearly the same thing, which is the basis of real sensor-voting schemes. They legitimately differ by up to ~20 K during a severe transient though (node 2 lags node 1), so a naive disagreement threshold false-alarms, which is worth thinking about.
- **`rod_reactivity` is measured and ignored.** Nothing consumes it. It could detect a stuck or lagging rod directly, rather than inferring it from the power response.
- **The rods can only move power by about ±2%.** They are worth ±5e-4 in reactivity, and thermal feedback eats 2.475e-2 of reactivity per unit of power, so fully withdrawn sustains roughly `n = 1.020` and no more. Ask for `desired_n = 1.05` and the rod simply pins at its limit. This is why `load_step` only steps to 1.015. Real plants solve this with soluble boron for bulk reactivity and keep the rods for fine control. Adding a boron term, or just widening the rod worth, is a legitimate change to make.
- **The PID is P-only** (`ki=0, kd=0`). Because the rod position integrates the speed command, proportional alone already removes steady-state error, so this is less broken than it looks, but there is still plenty of room in the transient.
- **No scoring harness.** There's no automated way to sweep every scenario and compare two controllers numerically. Building one makes every other change easier to justify.

---

## How Real Reactors Do This

Worth knowing where the starter is faithful and where it simplifies. The
description below follows Wang et al., *[Small Modular Reactors: An Overview of
Modeling, Control, Simulation, and Applications](https://ieeexplore.ieee.org/document/10384339)*,
IEEE Access 2024. Section II.C covers light water reactor control.

**What we model the same way:**

- **Rod speed, not rod position.** A real plant feeds a *rod velocity control unit* that determines "control rod movement speed and direction." That's exactly the interface `Controller.update()` implements.
- **Negative reactivity feedback.** The paper is explicit that cores are designed so rising temperature *reduces* reactivity, because the opposite is a runaway. Our `alpha_fuel` and `alpha_cool` are both negative for this reason.
- **Filtering to stop the rods hunting.** Real designs include a filter to "eliminate small and abrupt disturbance signals, preventing frequent movement of control rods." Feeding the controller the EKF estimate rather than the raw reading does the same job here.

**What we simplify:**

- **We regulate power; real PWRs regulate coolant temperature.** Standard schemes are constant steam pressure, constant *average coolant temperature*, or constant coolant outlet temperature. Power is an *input* to the setpoint program, not the regulated variable. Re-targeting this controller at coolant temperature, with a setpoint scheduled from requested power, would be a genuinely realistic upgrade.
- **Real control is three channels, not one.** A PWR combines a temperature measurement channel (with lead/lag compensation for the thermal inertia of the measurement itself), a reference setpoint channel, and a power-mismatch channel that acts when power has moved but temperature has not caught up yet. We have only the equivalent of the third.
- **No soluble boron.** Bulk excess reactivity is handled chemically in a real PWR, with rods left largely withdrawn during normal operation. Our single rod does everything, which is why its authority is so limiting.

---

## Roadmap

These milestones describe what already works in this folder and what to verify or build on next. They're guides, not a scoring checklist.

### Milestone 1: Run the Reactor Simulation

- Read the [point kinetics equations](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/point-kinetics-equations/), then read `reactor/model.py`'s `neutron_equations` and `thermal_equations`.
- Run `python run_scenario.py --scenario nominal` and inspect the plots.
- Identify the control input (`Controller.update` returns a rod speed), the sensor outputs (`SensorSuite`'s five channels), and the hidden values nothing measures directly (the six precursor concentrations `C1` to `C6`, and the two coolant-node temperatures).

Good demo: explain how the model responds when `rho_rod` changes, and why the six precursor groups matter for how fast power can change.

### Milestone 2: Build a Basic Power Controller

- `controller/control.py` implements an anti-windup PID on rod speed; it currently runs as P-only with `kp=3e-4`.
- Run `--scenario load_step` and observe tracking, overshoot, and settling time. It reaches the setpoint to within about 0.07% in roughly 190 s.
- Try adding `ki`/`kd` and compare. See [how to tune a PID controller](https://www.digikey.com/en/maker/projects/how-to-tune-a-pid-controller/9ee9a111aef049af9f84f785779989ec).
- Turn `kp` up and watch the trade-off: tracking gets faster, but past about `1e-3` the rods spend most of their time pegged at maximum speed chasing sensor noise. That's a real failure mode, not a simulation artefact.

Good demo: the controller tracks a setpoint change without immediately violating safety limits.

### Milestone 3: Add Safety Logic

- `controller/state_machine.py`'s `SafetySupervisor` already implements the warn/limit/scram thresholds and rod-reactivity override, including the SCRAM latch.
- Run `--scenario severe_transient` to see the supervisor actually SCRAM and hold `SHUTDOWN`.
- Run `--scenario coolant_disturbance` to see it recover through WARNING/LIMITING without ever SCRAMming.

Good demo: explain why SCRAM latches instead of clearing itself once conditions look normal again, and what `scram_rho` represents physically.

### Milestone 4: Improve Instrumentation and State Estimation

- `estimation/ekf.py` estimates the full state (including the hidden precursor and coolant-node values) from four of the noisy sensor channels: power and the three temperatures. Start with [How a Kalman Filter Works, in Pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/) if the maths is unfamiliar.
- Compare a run with and without `--no-filter`, and check the estimation-error figure (true vs. measured vs. estimated).
- The process-noise matrix `Q` in `simulation._build_ekf` is the main lever on how well the estimate tracks. Try changing it and watch what happens.

Good demo: the controller performs better using the EKF estimate than raw noisy measurements alone.

### Milestone 5: Handle Disturbances and Faults

- Run each of `sensor_bias`, `sensor_dropout`, `stuck_rod`, and `delayed_rod` and watch what the controller does. It survives all four, but not always gracefully. In `sensor_bias` it ends up confidently holding the wrong power.
- **Detection is entirely up to you.** There is no fault-detection code in the starter. Getting the system to notice something is wrong, say which channel, and do something sensible about it is the substance of this milestone. See [Known Gaps](#known-gaps) for what makes it harder than it first looks.

Good demo: the controller rides out at least one fault without an unsafe excursion. If you build detection, it names the channel that is actually broken rather than one that merely looks broken.

### Milestone 6: Make Your Solution Unique

Possible directions, once you understand the baseline above:

- Better control: PID tuning, gain scheduling, LQR, or MPC in `controller/control.py`
- Better estimation: sensor fusion or bias estimation in `estimation/ekf.py`
- Better safety: more robust SCRAM logic or safety margins in `controller/state_machine.py`
- Better diagnostics: fault detection and isolation from scratch, since there's nothing there to start from
- Better visualization: a live dashboard instead of `run/plotting.py`'s static figures, or scenario comparison plots
- Better evaluation: an automated sweep across all `SCENARIOS` with a score breakdown

Good demo: a clear idea beyond the baseline, and why it improves control, safety, estimation, or interpretability.

---

## Resources

### Background Information

- [Point Kinetics Equations](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/point-kinetics-equations/): the neutron-population model `reactor/model.py` implements, including why delayed neutrons are what make a reactor controllable at all.
- [Reactor Dynamics](https://www.nuclear-power.com/nuclear-power/reactor-physics/reactor-dynamics/): broader context on reactivity, feedback, and transients.

### Technical Resources

- [How a Kalman Filter Works, in Pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/): the clearest visual introduction to Kalman filtering. Read this before `estimation/ekf.py`; it explains the predict/update cycle and what the covariance matrices are actually doing.
- [How to Tune a PID Controller](https://www.digikey.com/en/maker/projects/how-to-tune-a-pid-controller/9ee9a111aef049af9f84f785779989ec): practical tuning procedure for the `kp`/`ki`/`kd` gains in `controller/control.py`.
- [SciPy `solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html): the ODE integrator the model uses. The reactor is stiff, which is why it runs the `Radau` method rather than the default.
- [Matplotlib documentation](https://matplotlib.org/stable/index.html): for extending `run/plotting.py`.

### Additional References

- [Anti-windup for PID controllers](https://en.wikipedia.org/wiki/Integral_windup): why `controller/control.py` stops integrating once the rod saturates.
- [Extended Kalman Filter](https://en.wikipedia.org/wiki/Extended_Kalman_filter): the nonlinear generalisation used here, and the role of the Jacobian.
- [Fault detection and isolation](https://en.wikipedia.org/wiki/Fault_detection_and_isolation): background for the detection work left open in [Known Gaps](#known-gaps).
