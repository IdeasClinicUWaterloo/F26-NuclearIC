# SMR Reactor Design Optimization Tool

A Python + Streamlit application for exploring how SMR fuel rod design choices affect reactor performance, fuel lifetime, and fuel-cycle economics.

## What it does

This project allows users to:

- choose an SMR reactor type
- configure fuel rod geometry
- select fuel and structural materials
- compare fuel-cycle cost outcomes
- estimate rod replacement interval
- evaluate normalized economics such as **$/MWh**

## Main ideas behind the model

The application links:

1. **Geometry**  
   Rod length, rod diameter, and rod count affect fuel volume and heavy metal mass.

2. **Burnup physics**  
   Burnup is used to estimate the total thermal energy available from the fuel before replacement.

3. **Fuel-cycle economics**  
   The cost model uses representative front-end, fabrication, hardware, and backend cost assumptions to estimate:
   - core procurement cost
   - lifecycle fuel-cycle cost
   - normalized cost per MWh

4. **Optimization**  
   The project can be extended to optimize for metrics such as minimizing lifecycle $/MWh.

## Example outputs

- Core thermal power
- Rod count
- Rod change interval
- Core procurement cost
- Lifecycle total cost
- Lifecycle $/MWh

## Tech stack

- Python
- Streamlit
- Engineering-based calculation model
- Fuel-cycle cost assumptions inspired by INL / ORNL style references

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
