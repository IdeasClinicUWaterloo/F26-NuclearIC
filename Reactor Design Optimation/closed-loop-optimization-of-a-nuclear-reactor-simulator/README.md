# Manchester Nuclear Reactor Simulator Optimizer

An automated control and optimization framework for the Manchester Nuclear Reactor Simulator.

## Overview

This project explores how to programmatically control and optimize the Manchester Nuclear Reactor Simulator by treating it as a dynamic control system rather than just a browser game.

The work began by investigating whether the simulator exposed a traditional gameplay API. Instead of finding a clear backend control API, the simulator was found to be primarily client-side, with internal JavaScript objects exposing both live plant state and the control pathway.

Using that understanding, I built a browser-based controller that can:

* read live simulator state such as power demand, generator output, rod position, coolant flow, steam flow, core temperature, and coolant temperature
* apply control commands through the simulator’s instrument layer
* operate the level automatically using startup, tracking, and recovery logic
* generate competitive scores while maintaining safe plant behavior

The long-term goal of the project is to move from hand-tuned control logic toward automated parameter optimization and, potentially, reinforcement learning.

## Project Goals

* Reverse engineer the simulator’s controllable interface
* Build a closed-loop controller that can complete the level automatically
* Improve score by reducing power-demand tracking error
* Maintain safe operating behavior during startup, normal operation, and recovery
* Create a framework for automated controller tuning

## Key Technical Insight

The simulator does not behave like a simple static system where knob positions instantly determine final output.

Instead, it behaves like a dynamic control system with lag and internal state evolution:

1. A control command updates a UI instrument
2. The instrument manager copies that value into simulation inputs
3. The game loop advances the plant state over time
4. Output, temperature, and other values change gradually rather than instantly

Because of this, optimization is not about finding one fixed correct knob setting. It is about finding a control strategy that performs well over time under changing demand and safety constraints.

## System Architecture

### 1. State Monitoring

The controller reads live state from browser-exposed JavaScript objects, including:

* control rod position
* coolant flow rate
* steam flow rate
* reactor core temperature
* coolant temperature
* generator output
* generator output in MW
* power demand
* score and simulator status

### 2. Control Layer

The controller writes commands through the simulator’s instrument layer rather than directly overwriting display values.

Main control channels:

* coolant
* reactor rods
* steam generator

### 3. Control Policy

The current controller uses three operating modes:

* **Startup**: bring the reactor online safely
* **Tracking**: adjust rods and steam to follow changing demand
* **Recovery**: back away from unstable conditions and return to safe operation

### 4. Logging and Evaluation

Each run logs:

* state variables
* commanded control values
* score progression
* mode transitions
* demand tracking performance

This makes it possible to compare controller versions systematically.

## Current Approach

The present controller is a rule-based, hand-tuned baseline. It uses reactor state and demand/output error to determine how to move rods and steam while keeping coolant active and enforcing safety logic.

This baseline already demonstrates that the simulator can be played automatically and scored competitively. It also provides the foundation for automated tuning.

## Why There Is Not One Correct Answer

A common question is whether the simulator has one optimal solution.

The answer is no, because this is a dynamic trajectory optimization problem rather than a single static calculation.

Different controller parameter choices affect:

* startup aggressiveness
* recovery behavior
* response speed to demand changes
* thermal stability margins
* scoring tradeoffs between safety and tracking accuracy

That means multiple strategies can perform well, and optimization is about improving controller behavior over the full episode.

## Next Step: Automated Optimization

The next stage of the project is automated parameter tuning.

Instead of manually adjusting thresholds, gains, floors, and rate limits, an optimization algorithm can run repeated episodes and search for parameter sets that improve:

* final score
* peak score
* average absolute demand-tracking error
* percent of time spent within tolerance
* safe, non-tripping operation

This is the most practical next step because the project already has:

* a working controller
* measurable outputs
* a repeatable execution environment

## Potential Future Work

* Bayesian or black-box optimization of controller parameters
* Gain scheduling based on demand range or plant state
* A faster offline simulator for large-scale controller training
* Reinforcement learning for action selection over time
* Visualization dashboards for controller comparison and diagnostics

## Tech Stack

* **Python**
* **Playwright** for browser automation
* **JavaScript runtime inspection** for simulator state/control discovery
* **JSON/JSONL logging** for experiment tracking
* **Parameter optimization frameworks** such as Optuna or CMA-ES
* **Optional RL frameworks** for future controller learning

## Repository Structure

```text
.
├── window.py
├── observer.py
└── README.md
```

## Current Repository Files

### `observer.py`

This script was used during the reverse-engineering and inspection phase of the project.

Its main purpose is to observe how the Manchester Nuclear Reactor Simulator behaves inside the browser by collecting useful runtime information such as:

* network requests
* console messages
* page state
* browser-side simulator behavior

This helped determine that the simulator is primarily client-side and that the most useful control and monitoring pathways are exposed through browser-side JavaScript objects rather than a traditional public gameplay API.

### `window.py`

This script is the main browser interaction and automation layer for the project.

It is responsible for:

* opening the simulator in the browser
* reading live simulator state
* interacting with the simulator controls
* serving as the foundation for the automated controller

This file represents the current working base for automated gameplay and future controller tuning.

## Planned Additions

As the project develops further, the repository may be extended with additional files for:

* automated parameter optimization
* experiment analysis and comparison
* saved logs and controller evaluation tools

## Example Research Questions

* How much score improvement is possible through automated controller tuning?
* Which parameters have the highest effect on performance?
* Can startup and recovery be optimized independently from steady-state tracking?
* At what point does parameter optimization stop being enough and full reinforcement learning become worthwhile?

## Status

Current state of the project:

* client-side simulator structure identified
* control and monitoring pathways mapped
* working automated controller built
* repeatable logging established
* baseline score achieved
* ready for automated parameter optimization

## Disclaimer

This project is focused on simulator control and algorithmic optimization in an educational environment. It is not intended to model or represent real-world nuclear plant control practices.

## Author

**Souren Haghbin**

Mechatronics Engineering student exploring control, automation, optimization, and intelligent systems through dynamic simulation environments.
