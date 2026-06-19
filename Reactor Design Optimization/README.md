# Reactor Optimization

## Challenge Description

Small modular reactors are an emerging nuclear technology with the potential to improve deployment flexibility, reduce construction complexity, and support cleaner energy systems. However, designing and operating an SMR involves many trade-offs. Reactor performance depends on choices such as fuel type, fuel rod geometry, material selection, thermal power, control rod behavior, coolant flow, steam flow, startup strategy, cost, fuel lifetime, and safety margins.

The challenge in this subproblem is to optimize some part of a reactor system. Teams may focus on reactor design optimization, reactor operation optimization, or a combination of both. A strong solution should not simply choose one input value, but should explore trade-offs between performance, cost, efficiency, safety, and feasibility.

Students are invited to build models, dashboards, simulations, or optimization algorithms that help compare reactor choices and improve reactor behavior.

## Potential Project Directions

Teams may choose one focused direction or combine multiple approaches. Possible projects include:

- Reactor design comparison dashboard
- Lifecycle cost and deployment feasibility study
- Fuel and material trade-off analysis
- Design-space exploration tool for comparing many possible reactor designs
- Sensitivity analysis report showing which inputs most affect cost or performance
- Improved visualization dashboard for reactor costs, fuel lifetime, and trade-offs
- Automated reactor simulator controller for startup, demand tracking, and recovery
- Controller tuning optimizer for improving simulator score or stability
- Reactor simulation logging and performance analysis tool
- Combined design-and-operation optimization study
- Final recommendation memo or pitch deck for a proposed reactor design or operating strategy

## Ways to Approach This Challenge

This subproblem is intentionally open to multiple backgrounds. Teams are not expected to be nuclear engineers or controls experts. The goal is to use data, models, and reasoning to compare reactor options and make a clear recommendation.

### Science / Engineering Path
Focus on reactor design choices and physical trade-offs.

Possible directions:
- Compare fuel types such as UO2, MOX, and TRISO
- Study how fuel rod geometry affects fuel lifetime and power density
- Research SMR types and explain which design choices fit each reactor concept
- Add or justify safety constraints such as temperature limits or operating margins
- Create a technical proposal for a balanced reactor design

### Business / Economics Path
Focus on cost, deployment, and feasibility.

Possible directions:
- Compare upfront cost versus lifecycle cost
- Analyze which design choices create the biggest cost changes
- Build a dashboard for cost breakdowns and trade-offs
- Rank reactor designs by economic practicality
- Create a deployment recommendation for a specific use case such as remote power, industrial heat, or grid support

### Software / Data Path
Focus on tools, dashboards, and automated analysis.

Possible directions:
- Improve the design optimization dashboard
- Add sensitivity analysis and design-space exploration
- Build charts that explain the trade-offs clearly
- Automate the search for strong design options
- Export ranked results or comparison reports

### Controls / Simulation Path
Focus on reactor operation over time.

Possible directions:
- Build or improve an automated reactor simulator controller
- Tune startup, tracking, and recovery behavior
- Log simulator runs and compare controller versions
- Optimize controller parameters to improve score or stability

## Recommended Roadmap

Teams are encouraged to take the project in any direction. These milestones are not requirements or a scoring checklist; they are meant to give less experienced teams a practical path from running the model to implementing and upgrading it to their own solution. Advanced teams can skip, combine, or replace them with their own plan.

### Milestone 1: Understand the Reactor System

Goal: identify what inputs and outputs matter.

Suggested outcomes:

* Review the provided reactor design or simulator tools
* Identify controllable inputs such as fuel type, rod dimensions, materials, power level, coolant flow, steam flow, or control rod position
* Identify important outputs such as lifecycle cost, fuel lifetime, thermal power, generator output, temperature, tracking error, score, or safety status
* Explain what trade-off the team wants to optimize

Good demo: the team can explain what part of the reactor system they are optimizing and why it matters.

### Milestone 2: Run a Baseline Case

Goal: create a starting point that future improvements can be compared against.

Suggested outcomes:

* Run the provided design optimization model or reactor simulator
* Record baseline inputs and outputs
* Save key results such as cost, efficiency, fuel lifetime, score, or tracking error
* Identify weaknesses in the baseline design or control strategy

Good demo: the team can show a baseline result and describe what they want to improve.

### Milestone 3: Add Comparison Tools

Goal: make reactor trade-offs visible.

Suggested outcomes:

* Compare multiple fuel types, materials, geometries, or operating strategies
* Create tables showing how each choice affects cost and performance
* Add charts for cost breakdown, lifecycle cost, fuel lifetime, generator output, temperature, or tracking error
* Highlight the best-performing or most balanced options

Good demo: the tool clearly shows how changing an input affects reactor performance.

### Milestone 4: Perform Sensitivity Analysis

Goal: identify which parameters matter most.

Suggested outcomes:

* Change one input at a time and measure how outputs change
* Compare parameters such as rod length, rod diameter, rod count, fuel type, cladding material, power level, coolant behavior, or control gains
* Rank inputs by their effect on cost, efficiency, score, tracking error, or safety behavior
* Use results to decide where optimization should focus

Good demo: the team can show which inputs have the largest effect on reactor performance.

### Milestone 5: Build an Optimization Method

Goal: move from manual testing to automated search.

Suggested outcomes:

* Define an objective function, such as minimizing lifecycle cost, maximizing score, reducing tracking error, or balancing cost and fuel lifetime
* Search across design parameters, control parameters, or both
* Save and compare the best solutions found

Good demo: the system can automatically test multiple options and identify a better-performing design or strategy.

### Milestone 6: Evaluate Trade-Offs

Goal: show that the chosen solution is not just better in one metric, but understandable overall.

Suggested outcomes:

* Compare optimized and baseline results
* Show whether improvements in one metric cause drawbacks in another
* Discuss trade-offs such as higher upfront cost versus lower lifecycle cost, faster startup versus safety margin, or better demand tracking versus thermal stability
* Present results using tables, charts, or dashboards

Good demo: the team can explain why their optimized result is useful and what trade-offs it creates.

### Milestone 7: Make Your Solution Stand Out

Goal: turn the starter system into the team’s own solution.

Possible directions:

* Better design optimization: improve the cost model, add more materials, add constraints, or perform design-space exploration
* Better control optimization: improve startup, demand tracking, recovery, or controller parameter tuning
* Better analysis: add dashboards, sensitivity charts, run comparison tools, or result exports
* Better objective functions: balance multiple goals such as cost, performance, safety, and fuel lifetime
* Better automation: run large batches of experiments and save ranked results
* Better explanation: turn simulation results into a clear reactor design or operating proposal

Good demo: the project has a clear idea beyond the starter code and shows why that idea improves reactor optimization.

## Starter Package Overview

This folder contains starter material for the reactor optimization subproblem. It is intended as a base package that teams can extend during the event, not as a polished production system.

The starter material may support two broad solution paths:

1. Reactor design optimization
   Compare SMR design choices such as fuel rod geometry, material selection, fuel type, thermal power, cost, and fuel lifetime.

2. Reactor operation optimization
   Control a reactor simulator over time by adjusting operating inputs such as control rods, coolant flow, steam flow, and startup or recovery logic.

Teams may choose one path or combine both.

## Included Components

### SMR Reactor Design Optimization Tool

A design-focused tool for comparing reactor design choices.

This tool can be used to explore:

* fuel rod length
* rod outer diameter
* pellet diameter
* rod count
* fuel material
* cladding material
* guide tube material
* spacer material
* nozzle material
* SMR type
* thermal power
* capacity factor
* lifecycle cost
* fuel replacement interval
* normalized cost per MWh

Possible extensions include:

* fuel comparison charts
* material comparison charts
* cost breakdown tables
* sensitivity analysis
* design-space exploration
* top design rankings
* improved optimization objectives

### Manchester Nuclear Reactor Simulator Optimizer

An operation-focused tool for controlling a reactor simulator as a dynamic system.

This tool can be used to explore:

* live reactor state monitoring
* control rod movement
* coolant flow control
* steam flow control
* startup behavior
* demand tracking
* recovery behavior
* score improvement
* controller parameter tuning
* simulator run logging

Possible extensions include:

* automated controller tuning
* run comparison dashboards
* tracking-error analysis
* safety and recovery improvements
* black-box optimization
* reinforcement learning experiments

## Development Setup

### Python Environment

The Python starter code should be run inside a local virtual environment.

Suggested setup:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

If a requirements file is not provided yet, teams may need to install packages manually depending on their chosen solution path.

For design dashboards:

```bash
python -m pip install streamlit pandas plotly
```

For browser-based simulator automation:

```bash
python -m pip install playwright
python -m playwright install
```

For parameter optimization:

```bash
python -m pip install optuna
```

## Suggested Workflow

### 1. Choose an Optimization Focus

Decide whether the team is focusing on:

* reactor design optimization
* reactor operation/control optimization
* both design and operation

The project should have a clear optimization target.

Examples:

* minimize lifecycle cost per MWh
* maximize reactor simulator score
* reduce power-demand tracking error
* increase fuel replacement interval
* compare material and fuel choices
* balance upfront cost against long-term cost
* improve startup and recovery behavior

### 2. Run the Baseline Tool

Start with the provided model or simulator.

For design optimization:

* run the design dashboard
* record the default design
* note baseline cost and fuel lifetime

For operation optimization:

* run the reactor simulator automation
* record baseline score and tracking behavior
* note where the controller fails or performs poorly

### 3. Log Results

Optimization is difficult without measurable results.

Useful design metrics:

* core procurement cost
* operational cost per year
* maintenance cost per year
* lifecycle cost
* lifecycle cost per MWh
* fuel procurement cost per MWh
* rod replacement interval

Useful operation metrics:

* final score
* peak score
* generator output
* power demand
* average tracking error
* percent of time within tolerance
* core temperature
* coolant temperature
* shutdown status
* recovery events

### 4. Compare Alternatives

Before building a complex optimizer, compare a few simple alternatives.

Examples:

* UO2 vs MOX vs TRISO
* different rod diameters
* different rod counts
* different cladding materials
* fixed power vs power scaling
* conservative vs aggressive startup
* different steam or rod control gains

This helps identify which variables are worth optimizing.

### 5. Add Automated Search

Once the team has a baseline and metrics, automate the search.

Possible approaches:

* grid search over a small set of values
* random search over a larger range
* Bayesian optimization
* Optuna parameter tuning
* reinforcement learning for time-based control decisions

Teams should save the best results and compare them against the baseline.

### 6. Present the Trade-Offs

Strong solutions should explain the result, not just output a number.

A final demo should answer:

* What was optimized?
* What inputs were changed?
* What metric improved?
* What trade-offs were introduced?
* Was the optimized solution practical?
* What would be improved next?

## Example Research Questions

* Which design parameters most affect lifecycle reactor cost?
* Which materials produce the largest cost or fuel lifetime changes?
* Does a lower lifecycle cost require a higher upfront procurement cost?
* Which fuel type performs best under the current cost model?
* How sensitive is reactor cost to rod geometry?
* Which controller parameters most affect simulator score?
* Can startup and recovery be optimized separately from steady-state tracking?
* Does aggressive control improve demand tracking but increase instability?
* Can a combined design and operation strategy outperform either approach alone?
* At what point does parameter optimization stop being enough and reinforcement learning become worthwhile?

## Notes for Teams

This challenge is intentionally open-ended. There is not one correct answer.

For design optimization, a good solution may involve choosing a balanced design rather than the absolute cheapest design. For example, a design with higher upfront cost may have lower lifecycle cost or longer fuel lifetime.

For operation optimization, the simulator behaves like a dynamic control system. A single fixed control setting is usually not enough. Strong controllers should respond over time to demand, output, temperature, and safety conditions.

Teams should focus on clear comparisons, repeatable experiments, and explainable trade-offs.

## Status

Current state of the starter material:

* reactor design optimization prototype available
* reactor operation/control prototype available
* baseline design comparison possible
* automated simulator control demonstrated
* logging and evaluation can be extended
* ready for sensitivity analysis, dashboard improvements, and automated parameter optimization

## Disclaimer

This challenge is focused on educational simulation, design exploration, and algorithmic optimization. It is not intended to model, validate, or represent real-world nuclear plant design, licensing, operation, or safety practices.
