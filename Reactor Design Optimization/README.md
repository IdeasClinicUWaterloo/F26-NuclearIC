# Reactor Design Optimization

## Challenge

Small modular reactors (SMRs) involve trade-offs among performance, cost, efficiency, safety, and feasibility. Choices such as fuel, moderator, coolant, materials, fuel rod geometry, thermal power, control strategy, and flow rates can affect how a reactor is designed or operated.

Your challenge is to optimize one focused part of a reactor system. You may build a model, dashboard, simulation, controller, research study, or optimization algorithm. A strong project should compare alternatives and explain the trade-offs rather than identify a single input value as universally best.

This challenge supports two broad directions:

- **Design optimization:** compare choices such as fuel, materials, geometry, power, lifecycle cost, and fuel lifetime.
- **Operation optimization:** adjust control rods, coolant flow, steam flow, or controller parameters during startup, demand tracking, and recovery.

Teams may choose either direction or combine them.

## Potential Solutions

The supported solutions below provide working materials that teams can extend. The additional possibilities are independent ideas that teams may pursue from scratch or combine with a supported solution.

### Supported Solutions

| Supported Solution | Possible Directions | Resources |
| --- | --- | --- |
| **SMR Reactor Design Optimization Tool** | Set design parameters and examine their effects on reactor cost and efficiency. | [Design optimization tool](smr-reactor-design-optimizer/) |
| **Automated reactor controller** | Read the live state of a simulator and adjust control values to maximize efficiency. | [Manchester simulator optimizer](closed-loop-optimization-of-a-nuclear-reactor-simulator/) |

### Additional Possibilities

| Perspective | Possibility |
| --- | --- |
| Engineering | Apply **reactor optimization methods** to improve startup, tracking, recovery, or design performance. |
| Engineering | Create a **reactor comparison dashboard** for designs, simulator runs, costs, and performance metrics. |
| Engineering | Build a **reactor data analysis system** to identify which design or control parameters affect performance most. |
| Engineering | Research an **SMR design concept** and develop a proposal for a particular reactor design. |
| Science | Conduct a **reactor-channel flow investigation** using safe surrogate systems to model coolant movement and heat removal through reactor channels. |
| Science | Create a **cost-optimization strategy** for the plant. |
| Science | Perform a **component lifespan study** examining how temperature, flow, load cycles, and other operating conditions influence longevity. |
| Science | Create a **reactor efficiency map** relating coolant flow, temperature, and power output to identify efficient operating ranges. |
| Science | Complete a **reactor lifecycle optimization study** examining how design choices affect long-term performance, maintenance needs, and operating efficiency. |

Projects can emphasize science and engineering, business and economics, software and data, or controls and simulation. Teams should still connect their work to relevant physical constraints and include at least 20% science and engineering in their solution.

## Starter Tools

### SMR Reactor Design Optimization Tool

The [SMR Reactor Design Optimization Tool](smr-reactor-design-optimizer/) is a Python and Streamlit application for comparing a subset of reactor design choices. Its default model uses a BWRX-300-style light-water SMR as a worked example.

The tool includes inputs for fuel rod geometry, fuel and structural materials, thermal power, and capacity factor. It estimates outputs such as core procurement cost, lifecycle cost, fuel replacement interval, and normalized cost per MWh.

Possible extensions include sensitivity charts, material comparisons, design-space exploration, improved cost or constraint models, and ranked design recommendations. See the [tool README](smr-reactor-design-optimizer/README.md) for details.

### Manchester Nuclear Reactor Simulator Optimizer

The [Manchester Nuclear Reactor Simulator Optimizer](closed-loop-optimization-of-a-nuclear-reactor-simulator/) is a browser-based framework for treating the Manchester simulator as a dynamic control problem.

It can read reactor state, apply control commands, automate startup and demand tracking, and log performance. Possible extensions include automated controller tuning, run-comparison dashboards, tracking-error analysis, recovery improvements, black-box optimization, or reinforcement-learning experiments.

See the [simulator optimizer README](closed-loop-optimization-of-a-nuclear-reactor-simulator/README.md) for its architecture and current status.

## Recommended Workflow

These steps are guidance, not requirements. Advanced teams may replace them with their own process.

### 1. Choose a Focus

Define the part of the system you want to improve and the metric you will use to evaluate it.

Example objectives include:

- minimize lifecycle cost per MWh
- increase fuel replacement interval
- maximize simulator score
- reduce power-demand tracking error
- improve startup or recovery behavior
- balance cost, performance, and safety constraints

### 2. Establish a Baseline

Run the starter tool or simulator with its current settings. Save the important inputs and outputs so later changes can be compared fairly.

Useful design metrics include lifecycle cost, cost per MWh, procurement cost, fuel lifetime, and power density. Useful operation metrics include score, generator output, tracking error, time within tolerance, temperatures, shutdown state, and recovery events.

### 3. Compare Alternatives

Test a small number of meaningful alternatives before building a complex optimizer. For example, compare fuel types, rod dimensions, materials, power levels, startup strategies, or controller gains.

Use tables or charts to show how each input affects the results. A simple sensitivity analysis can reveal which variables are worth optimizing.

### 4. Automate the Search

Define an objective function and constraints, then search across the most important parameters. Depending on the project, this could use a grid search, random search, Bayesian optimization, Optuna, or another justified method.

Save the best candidates and compare them with the baseline. Avoid optimizing only one number if doing so creates an impractical or unsafe result.

### 5. Explain the Recommendation

Your final demonstration should answer:

- What did you optimize, and why?
- Which inputs changed?
- Which metric improved, and by how much?
- What constraints or assumptions did you use?
- What trade-offs or drawbacks did the change introduce?
- What would you improve with more time?

## Development Setup

Create and activate a virtual environment before installing dependencies.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Run the Design Tool

```powershell
cd smr-reactor-design-optimizer
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Run the Simulator Automation

```powershell
cd closed-loop-optimization-of-a-nuclear-reactor-simulator
python -m pip install playwright
python -m playwright install
python window.py
```

The simulator optimizer interacts with an external educational simulator. Review its README and code before running it.

## What Makes a Strong Solution

A strong project does not need to be the most complex one. It should:

- define a focused and measurable problem
- use relevant physics or engineering reasoning
- compare results against a baseline
- consider safety limits, feasibility, and edge cases
- make experiments repeatable
- explain assumptions and model limitations
- present trade-offs clearly

A balanced design may be more useful than the cheapest design. Likewise, a controller with slightly slower response may be preferable if it is more stable or maintains a larger safety margin.

## Research Starting Points

Questions you could investigate include:

- Which design parameters most affect lifecycle cost or fuel lifetime?
- How sensitive are results to fuel rod geometry or material assumptions?
- Does lower lifecycle cost require higher upfront cost?
- Which controller parameters most affect tracking error or simulator score?
- Can startup, steady-state tracking, and recovery be optimized separately?
- Does aggressive control improve tracking while reducing stability margins?
- How would the preferred design change for grid power, remote power, or industrial heat?

For information on current SMR concepts, consult the [OECD Nuclear Energy Agency SMR Dashboard](https://www.oecd-nea.org/upload/docs/application/pdf/2025-09/web_-_smr_dashboard_-_third_edition.pdf) and the [IAEA ARIS SMR Catalogue](https://aris.iaea.org/Publications/SMR_catalogue_2024.pdf).

## Disclaimer

This challenge is intended for educational simulation, design exploration, and algorithmic optimization. The starter models simplify real systems and are not intended to design, validate, license, operate, or represent the safety practices of a real nuclear plant.
