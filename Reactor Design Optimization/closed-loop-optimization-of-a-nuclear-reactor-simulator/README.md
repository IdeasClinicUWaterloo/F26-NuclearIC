# Manchester Nuclear Reactor Simulator Optimizer

A browser-based control and optimization framework for the educational Manchester Nuclear Reactor Simulator.

## Overview

The project treats the simulator as a dynamic control system. It reads live plant state, applies commands through the simulator's browser-side instrument layer, and uses startup, tracking, and recovery logic to operate a level automatically.

Unlike a static optimization problem, control changes do not produce their final effect immediately. The simulated plant evolves over time, so a successful strategy must respond to demand, output, temperature, lag, and safety conditions throughout an episode.

## Current Capabilities

The framework can:

- read control rod position, coolant flow, steam flow, temperatures, generator output, demand, score, and simulator status
- command rods, coolant, and steam through the instrument controls
- switch among startup, demand-tracking, and recovery modes
- log state, commands, scores, and mode changes for later analysis
- provide a repeatable baseline for controller tuning

The current controller is rule-based and hand-tuned. It demonstrates automated operation but is intended as a starting point for experimentation rather than a finished optimal controller.

## Project Files

- `window.py` opens the simulator, reads live state, applies controls, and runs the baseline controller.
- `observer.py` records browser and simulator behavior used to identify the available state and control pathways.
- `logs/` stores experiment output.

## Run Locally

From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install playwright
python -m playwright install
python window.py
```

The script connects to an external educational simulator. Its browser-side structure may change independently of this repository, so review the selectors and JavaScript access paths if the controller stops working.

## Evaluation Metrics

Useful metrics for comparing controllers include:

- final and peak score
- average demand-tracking error
- percentage of time within tolerance
- startup time and recovery time
- temperature excursions or shutdown events
- stability across repeated runs

## Suggested Next Steps

The most direct extension is automated tuning of controller thresholds, gains, floors, and rate limits. A team could use grid search, Bayesian optimization, Optuna, or another black-box method to run repeated episodes and compare parameter sets.

Other possible extensions include:

- separate tuning for startup, tracking, and recovery
- run-comparison and diagnostic dashboards
- gain scheduling based on demand or plant state
- a faster offline model for large experiment batches
- reinforcement learning for time-based action selection

Any optimizer should compare results with the baseline and consider stability and simulated safety behavior rather than optimizing score alone.

## Disclaimer

This project controls an educational browser simulator. It does not model or represent real-world nuclear plant control, operation, licensing, or safety practices.
