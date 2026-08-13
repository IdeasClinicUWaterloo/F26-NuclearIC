# SMR Reactor Design Optimization Tool

A Python and Streamlit application for exploring how fuel rod design choices affect estimated reactor performance, fuel lifetime, and fuel-cycle economics.

## What It Does

The dashboard lets users:

- select an SMR reference type
- configure fuel rod geometry and rod count
- choose fuel and structural materials
- estimate fuel replacement intervals
- compare procurement and lifecycle fuel-cycle costs
- evaluate normalized cost per MWh

The model connects geometry, burnup assumptions, and representative cost inputs. Rod dimensions and count determine estimated fuel volume and heavy-metal mass; burnup estimates available thermal energy before replacement; and the cost model estimates procurement, lifecycle, and normalized costs.

## Run Locally

From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Project Files

- `app.py` provides the Streamlit interface.
- `model.py` contains the engineering and cost calculations.
- `requirements.txt` lists the Python dependencies.
- `docs/` contains supporting documentation and references.

## Possible Extensions

- sensitivity analysis for geometry, materials, and power assumptions
- fuel and material comparison charts
- constrained design-space search
- ranked design recommendations
- clearer cost breakdowns and exports
- improved physics, cost assumptions, and validation

## Model Scope

The default configuration is a BWRX-300-style light-water SMR used as an educational reference point. The calculations are simplified and depend on model assumptions; outputs should be presented as comparative estimates rather than validated reactor predictions.

## Disclaimer

This tool is intended for educational design exploration. It is not suitable for real-world nuclear design, licensing, operation, or safety analysis.
