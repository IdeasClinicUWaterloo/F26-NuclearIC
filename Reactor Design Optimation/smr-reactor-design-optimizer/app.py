import streamlit as st
import pandas as pd
from model import RodDesign, estimate_costs_and_interval, REF


# Simple function to format large dollar values in a more readable way
def money_short(value):
    if value >= 10_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def optimize_design(
    base_design,
    rod_min,
    rod_max,
    diam_min,
    diam_max,
    scenario,
    capacity_factor,
    power_mode,
    core_power,
    gap,
):
    best_score = float("inf")
    best_results = None
    best_design = None

    for rods in range(int(rod_min), int(rod_max) + 1, 20):

        for diam in [
            diam_min + i * 0.0005
            for i in range(int((diam_max - diam_min) / 0.0005) + 1)
        ]:

            pellet_d = diam - 2 * (base_design.clad_thickness_m + gap)

            if pellet_d <= 0:
                continue

            design = RodDesign(
                length_m=base_design.length_m,
                outer_diameter_m=diam,
                pellet_diameter_m=pellet_d,
                clad_thickness_m=base_design.clad_thickness_m,
                num_rods=rods,
                pellet_material=base_design.pellet_material,
                cladding_material=base_design.cladding_material,
                guide_tube_material=base_design.guide_tube_material,
                spacer_material=base_design.spacer_material,
                nozzle_material=base_design.nozzle_material,
                smr_type=base_design.smr_type,
            )

            results = estimate_costs_and_interval(
                design,
                scenario=scenario,
                capacity_factor=capacity_factor,
                power_mode=power_mode,
                core_power_MWt=core_power,
            )

            score = results["normalized"]["lifecycle_$per_MWh_th"]

            if score < best_score:
                best_score = score
                best_results = results
                best_design = design

    return best_design, best_results


st.set_page_config(page_title="SMR Reactor Cost Optimization", layout="wide")

st.title("SMR Fuel Rod Optimizer")

# Cost scenario dropdown
# Displays Low / Mean / High, but passes low / mean / high into model.py
scenario = st.selectbox(
    "Cost Scenario",
    ["low", "mean", "high"],
    index=1,
    format_func=lambda x: x.title(),
)

left, right = st.columns(2)

with left:

    smr_type = st.selectbox(
        "SMR Type",
        [
            "Light Water Reactor",
            "Sodium Cooled SMRs",
            "High-Temperature Gas-Cooled SMRs",
            "Molten-Salt SMRs",
        ],
    )

    st.markdown("### Geometry")

    length = st.number_input("Rod length (m)", 0.5, 6.0, 3.7)

    outer_d = st.number_input(
        "Rod outer diameter (m)",
        0.005,
        0.05,
        REF["clad_od_m"],
    )

    clad_t = REF["clad_thickness_m"]

    gap = (
        REF["clad_od_m"]
        - 2 * REF["clad_thickness_m"]
        - REF["pellet_d_m"]
    ) / 2

    pellet_d = outer_d - 2 * (clad_t + gap)

    if pellet_d <= 0:
        st.error("Rod diameter too small for cladding thickness")
        st.stop()

    st.caption(f"Pellet diameter = {pellet_d:.6f} m")

    rods = st.number_input("Number of rods", 1, 20000, 264)

    st.markdown("### Materials")

    pellet = st.selectbox("Fuel", ["UO2", "MOX", "TRISO"])

    clad = st.selectbox(
        "Cladding",
        ["Zircaloy", "SS316", "Inconel", "Hastelloy"],
    )

    guide = st.selectbox(
        "Guide tube",
        ["Zircaloy", "SS316", "Inconel"],
    )

    spacer = st.selectbox(
        "Spacer",
        ["SS316", "Inconel", "Graphite"],
    )

    nozzle = st.selectbox(
        "Nozzle",
        ["SS316", "Inconel", "Hastelloy"],
    )


design = RodDesign(
    length_m=length,
    outer_diameter_m=outer_d,
    pellet_diameter_m=pellet_d,
    clad_thickness_m=clad_t,
    num_rods=rods,
    pellet_material=pellet,
    cladding_material=clad,
    guide_tube_material=guide,
    spacer_material=spacer,
    nozzle_material=nozzle,
    smr_type=smr_type,
)


with right:

    # -------------------------
    # OPERATION SETTINGS
    # -------------------------

    st.markdown("### Operation")

    power_mode = st.selectbox(
        "Power model",
        ["fixed_core_power", "scale_with_N"],
        format_func=lambda x: "Fixed reactor power"
        if x == "fixed_core_power"
        else "Power scales with rod count",
    )

    capacity_factor = st.slider("Capacity factor", 0.5, 1.0, 0.9)

    core_power = None

    if power_mode == "fixed_core_power":
        core_power = st.number_input(
            "Core thermal power (MWt)",
            min_value=1.0,
            max_value=5000.0,
            value=1000.0,
        )

    # -------------------------
    # OPTIMIZATION SETTINGS
    # -------------------------

    st.markdown("### Optimization")

    run_optimizer = st.checkbox("Optimize design (minimize lifecycle $/MWh)")

    if run_optimizer:

        st.markdown("Optimization search space")

        rod_min = st.number_input("Min rods", 50, 2000, 100)
        rod_max = st.number_input("Max rods", 50, 2000, 600)

        diam_min = st.number_input("Min rod diameter (m)", 0.007, 0.02, 0.008)
        diam_max = st.number_input("Max rod diameter (m)", 0.007, 0.02, 0.012)

        if rod_min > rod_max:
            st.error("Minimum rod count cannot be greater than maximum rod count.")
            st.stop()

        if diam_min > diam_max:
            st.error("Minimum rod diameter cannot be greater than maximum rod diameter.")
            st.stop()

    # -------------------------
    # RESULTS
    # -------------------------

    if run_optimizer:

        best_design, results = optimize_design(
            design,
            rod_min,
            rod_max,
            diam_min,
            diam_max,
            scenario=scenario,
            capacity_factor=capacity_factor,
            power_mode=power_mode,
            core_power=core_power,
            gap=gap,
        )

        st.success("Optimization complete")

        st.write("Best design found:")
        st.write("Rod count:", best_design.num_rods)
        st.write("Rod diameter:", best_design.outer_diameter_m)

    else:

        results = estimate_costs_and_interval(
            design,
            scenario=scenario,
            capacity_factor=capacity_factor,
            power_mode=power_mode,
            core_power_MWt=core_power,
        )

    st.markdown("### Results (Estimated)")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Core thermal power (MWt)", f"{results['core_power_MWt']:.1f}")
        st.metric("Rod count", results["num_rods"])
        st.metric(
            "Rod change interval",
            f"{results['rod_change_interval_years']:.2f} yrs",
        )

    with c2:
        st.metric(
            "Core procurement cost",
            money_short(results["installation_cost"]),
        )
        st.metric(
            "Operational cost / year",
            money_short(results["operational_cost_per_year"]),
        )
        st.metric(
            "Maintenance cost / year",
            money_short(results["maintenance_cost_per_year"]),
        )

    with c3:
        st.metric(
            "Lifecycle $/MWh (thermal)",
            f"${results['normalized']['lifecycle_$per_MWh_th']:.2f}",
        )

        st.metric(
            "Lifecycle $/MWh (electric)",
            f"${results['normalized']['lifecycle_$per_MWh_e']:.2f}",
        )

        st.metric(
            "Fuel procurement $/MWh",
            f"${results['normalized']['procurement_$per_MWh_e']:.2f}",
        )

# Make a table of the different fuel components and how they affect cost
st.markdown("### Fuel Type Comparison")

#We need to run through the different fuel types, keeping all other parameter the same
#We need to collect the results in a dataframe, then make a table for lifecycle $/MWh, procurement, and maintenance

fuel_rows = []

for fuel in ["UO2", "MOX", "TRISO"]:

  

    #Make the design first
    compare_design = RodDesign(
    length_m=length,
    outer_diameter_m=outer_d,
    pellet_diameter_m=pellet_d,
    clad_thickness_m=clad_t,
    num_rods=rods,
    pellet_material=fuel,
    cladding_material=clad,
    guide_tube_material=guide,
    spacer_material=spacer,
    nozzle_material=nozzle,
    smr_type=smr_type,
)
    
    #Then get the results

    compare_results = estimate_costs_and_interval(
        compare_design,
        scenario=scenario,
        capacity_factor=capacity_factor,
        power_mode=power_mode,
        core_power_MWt=core_power,
    )

    fuel_rows.append(
        {
            "Fuel": fuel,
            "Lifecycle $/MWh (thermal)": compare_results["normalized"]["lifecycle_$per_MWh_th"],
            "Lifecycle $/MWh (electric)": compare_results["normalized"]["lifecycle_$per_MWh_e"],
            "Fuel procurement $/MWh": compare_results["normalized"]["procurement_$per_MWh_e"],
            "Rod change interval (yrs)": compare_results["rod_change_interval_years"],
            "Core procurement cost": compare_results["installation_cost"],
            "Operational cost / year": compare_results["operational_cost_per_year"],
            "Maintenance cost / year": compare_results["maintenance_cost_per_year"],
        }
    )

fuel_df = pd.DataFrame(fuel_rows)
    
st.dataframe(fuel_df.style.format({
        "Lifecycle $/MWh (thermal)": "${:,.2f}",
        "Lifecycle $/MWh (electric)": "${:,.2f}",
        "Fuel procurement $/MWh": "${:,.2f}",
        "Core procurement cost": "${:,.2f}",
        "Operational cost / year": "${:,.2f}",
        "Maintenance cost / year": "${:,.2f}",
    }))


# Make a graph of sensitivity analysis 

