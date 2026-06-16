from dataclasses import dataclass
import math
from typing import Dict, Literal, Optional

Scenario = Literal["low", "mean", "high"]
PowerMode = Literal["fixed_core_power", "scale_with_N"]

# -----------------------------
# Reference assembly (ORNL 17×17) used for calibration/allocations
# -----------------------------
REF = {
    "N_rods": 264,
    "kgU_per_assembly": 459.52,
    "kgU_per_rod": 459.52 / 264.0,  # 1.7406 kgU/rod
    "L_m": 3.6576,
    "pellet_d_m": 0.0081915,
    "clad_od_m": 0.0094996,
    "clad_thickness_m": 0.0005715,
    "guide_tubes_mass_per_assembly_kg": 9.526,
    "spacers_mass_per_assembly_kg": 6.0,
    "nozzles_mass_per_assembly_kg": 12.0,  # top+bottom combined
}

# -----------------------------
# INL WIT-style cost modules (from your deep research PDF)
# Units: $/kgU (front-end & fab), $/kgHM for back-end
# -----------------------------
WIT_UO2 = {
    "mining_milling": {"low": 41.5, "mean": 168.5, "high": 360.0},  # $/kgU
    "conversion": {"low": 7.0, "mean": 13.8, "high": 20.8},         # $/kgU
    "enrichment": {"low": 119, "mean": 153, "high": 188},           # $/kgU-eq
    "fabrication": {"low": 281, "mean": 491, "high": 702},          # $/kgU
    "interim_store": {"low": None, "mean": 186, "high": None},      # $/kgHM
    "transport_repo": {"low": None, "mean": 32, "high": None},      # $/kgHM proxy
    "geologic_disp": {"low": None, "mean": 709, "high": None},      # $/kgHM
}

WIT_MOX = {
    "fabrication": {"low": 822, "mean": 1178, "high": 1660},        # $/kgHM
    "reprocessing_proxy": {"low": None, "mean": None, "high": None} # calibrated below
}

WIT_TRISO = {
    "haleu_product": {"low": 8200, "mean": 15500, "high": 25500},   # $/kgU
    "triso_fab": {"low": 1000, "mean": 4667, "high": 9000},         # $/kgU
}

# Fabrication allocator (for later UI breakdown if you want)
FAB_ALLOC_UO2 = {
    "pellets": 0.28,
    "rod_ops": 0.32,
    "assembly_ops": 0.23,
    "packaging_scrap": 0.07,
    "qa_reg": 0.10,
}

# -----------------------------
# Hardware cost proxies ($/kg of fabricated nuclear component)
# -----------------------------
HARDWARE_COST_PER_KG = {
    "Zircaloy": 420.0,
    "SS316": 310.0,
    "Inconel": 430.0,
    "Hastelloy": 430.0,
    "Graphite": 80.0,
}

# Densities (kg/m^3) for mass estimates
MATERIAL_DENSITY = {
    "Zircaloy": 6550.0,
    "SS316": 8000.0,
    "Inconel": 8470.0,
    "Hastelloy": 8900.0,
    "Graphite": 1800.0,
}

# -----------------------------
# SMR defaults (q' typical + burnup default)
# -----------------------------
SMR_DEFAULTS = {
    "Light Water Reactor": {"qprime_kW_per_m": 18.0, "burnup_GWd_tHM": 45.0, "risk": 1.0, "ops_mult": 1.0, "maint_mult": 1.0},
    "Sodium Cooled SMRs": {"qprime_kW_per_m": 20.0, "burnup_GWd_tHM": 55.0, "risk": 1.2, "ops_mult": 1.1, "maint_mult": 1.15},
    "High-Temperature Gas-Cooled SMRs": {"qprime_kW_per_m": 10.0, "burnup_GWd_tHM": 80.0, "risk": 1.1, "ops_mult": 1.05, "maint_mult": 1.05},
    "Molten-Salt SMRs": {"qprime_kW_per_m": 15.0, "burnup_GWd_tHM": 60.0, "risk": 1.25, "ops_mult": 1.15, "maint_mult": 1.2},
}

# -----------------------------
# Geometry helpers + calibrated effective uranium densities
# -----------------------------
def _cyl_volume(diameter_m: float, length_m: float) -> float:
    r = diameter_m / 2.0
    return math.pi * r * r * length_m

_REF_PELLET_VOL = _cyl_volume(REF["pellet_d_m"], REF["L_m"])
RHO_U_EFF = REF["kgU_per_rod"] / _REF_PELLET_VOL  # kgU per m^3 effective

# TRISO calibration from paper: 0.0964 kgU per rod (PF=0.3 proxy)
TRISO_REF_KGU_PER_ROD = 0.0964
RHO_TRISO_U_EFF = TRISO_REF_KGU_PER_ROD / _REF_PELLET_VOL

def _pick(d: Dict[str, Optional[float]], scenario: Scenario) -> float:
    v = d.get(scenario)
    return d["mean"] if v is None else float(v)

def _density(mat: str) -> float:
    return float(MATERIAL_DENSITY.get(mat, 8000.0))

def _hw_cost_per_kg(mat: str) -> float:
    return float(HARDWARE_COST_PER_KG.get(mat, HARDWARE_COST_PER_KG["SS316"]))

@dataclass
class RodDesign:
    length_m: float
    outer_diameter_m: float
    pellet_diameter_m: float
    clad_thickness_m: float
    num_rods: int
    pellet_material: str
    cladding_material: str
    guide_tube_material: str
    spacer_material: str
    nozzle_material: str
    smr_type: str

def heavy_metal_mass_per_rod_kg(fuel: str, pellet_d_m: float, L_m: float) -> float:
    vol = _cyl_volume(pellet_d_m, L_m)
    if fuel in ("UO2", "MOX"):
        return RHO_U_EFF * vol
    if fuel == "TRISO":
        return RHO_TRISO_U_EFF * vol
    raise ValueError(f"Unknown fuel: {fuel}")

def allocated_hardware_mass_per_rod_kg(N_rods: int) -> Dict[str, float]:
    return {
        "guide": REF["guide_tubes_mass_per_assembly_kg"] / max(1, N_rods),
        "spacers": REF["spacers_mass_per_assembly_kg"] / max(1, N_rods),
        "nozzles": REF["nozzles_mass_per_assembly_kg"] / max(1, N_rods),
    }

def cladding_mass_per_rod_kg(outer_d_m: float, L_m: float, clad_t_m: float, cladding_mat: str) -> float:
    inner_d = max(0.0, outer_d_m - 2.0 * clad_t_m)
    vol = max(0.0, _cyl_volume(outer_d_m, L_m) - _cyl_volume(inner_d, L_m))
    return vol * _density(cladding_mat)

def _calibrate_mox_reproc_proxy_mean() -> float:
    """
    Calibrate reprocessing proxy so that at reference geometry:
    lifecycle per rod ≈ 5927 USD/rod for 1.7406 kgHM/rod (paper anchor).
    """
    m = REF["kgU_per_rod"]
    target = 5927.0
    backend = (WIT_UO2["interim_store"]["mean"] + WIT_UO2["transport_repo"]["mean"] + WIT_UO2["geologic_disp"]["mean"]) * m
    fab = WIT_MOX["fabrication"]["mean"] * m
    needed = (target - backend - fab) / m
    return max(0.0, needed)

# Fill MOX proxy if empty
if WIT_MOX["reprocessing_proxy"]["mean"] is None:
    mean_proxy = _calibrate_mox_reproc_proxy_mean()
    WIT_MOX["reprocessing_proxy"]["mean"] = mean_proxy
    WIT_MOX["reprocessing_proxy"]["low"] = mean_proxy * 0.7
    WIT_MOX["reprocessing_proxy"]["high"] = mean_proxy * 1.3

def estimate_costs_and_interval(
    d: RodDesign,
    scenario: Scenario = "mean",
    include_backend: bool = True,
    capacity_factor: float = 0.9,
    burnup_GWd_tHM: Optional[float] = None,
    power_mode: PowerMode = "scale_with_N",
    core_power_MWt: Optional[float] = None,
    hardware_share_in_toll: float = 0.30,
    fixed_ops_per_year_usd: float = 0.0,
) -> Dict:

    smr = SMR_DEFAULTS[d.smr_type]
    qprime = smr["qprime_kW_per_m"]
    burnup = float(burnup_GWd_tHM) if burnup_GWd_tHM is not None else float(smr["burnup_GWd_tHM"])

    # ---------- Solve power / rod count depending on mode ----------
    if power_mode == "fixed_core_power":
        if core_power_MWt is None:
            raise ValueError("core_power_MWt must be provided in fixed_core_power mode.")
        P_core_kW = max(1.0, float(core_power_MWt) * 1000.0)
        # size rod count so that assumed q' holds
        N_req = max(1, int(math.ceil(P_core_kW / (qprime * d.length_m))))
        d = RodDesign(**{**d.__dict__, "num_rods": N_req})
    else:
        # scale_with_N
        P_core_kW = max(1.0, d.num_rods * qprime * d.length_m)

    core_power_MWt_out = P_core_kW / 1000.0

    # ---------- Masses ----------
    mHM_rod = heavy_metal_mass_per_rod_kg(d.pellet_material, d.pellet_diameter_m, d.length_m)
    mHM_total = mHM_rod * d.num_rods

    hw_alloc = allocated_hardware_mass_per_rod_kg(d.num_rods)
    m_clad = cladding_mass_per_rod_kg(d.outer_diameter_m, d.length_m, d.clad_thickness_m, d.cladding_material)

    # ---------- Hardware cost (THIS is where materials matter) ----------
    C_hw_rod = (
        m_clad * _hw_cost_per_kg(d.cladding_material)
        + hw_alloc["guide"] * _hw_cost_per_kg(d.guide_tube_material)
        + hw_alloc["spacers"] * _hw_cost_per_kg(d.spacer_material)
        + hw_alloc["nozzles"] * _hw_cost_per_kg(d.nozzle_material)
    )
    C_hw_total = C_hw_rod * d.num_rods

    # ---------- Fuel-cycle unit costs ----------
    if d.pellet_material == "UO2":
        c_front = _pick(WIT_UO2["mining_milling"], scenario) + _pick(WIT_UO2["conversion"], scenario) + _pick(WIT_UO2["enrichment"], scenario)
        c_fab_total = _pick(WIT_UO2["fabrication"], scenario)
        c_backend = _pick(WIT_UO2["interim_store"], scenario) + _pick(WIT_UO2["transport_repo"], scenario) + _pick(WIT_UO2["geologic_disp"], scenario)
    elif d.pellet_material == "MOX":
        c_front = _pick(WIT_MOX["reprocessing_proxy"], scenario)
        c_fab_total = _pick(WIT_MOX["fabrication"], scenario)
        c_backend = _pick(WIT_UO2["interim_store"], scenario) + _pick(WIT_UO2["transport_repo"], scenario) + _pick(WIT_UO2["geologic_disp"], scenario)
    elif d.pellet_material == "TRISO":
        c_front = _pick(WIT_TRISO["haleu_product"], scenario)
        c_fab_total = _pick(WIT_TRISO["triso_fab"], scenario)
        c_backend = _pick(WIT_UO2["interim_store"], scenario) + _pick(WIT_UO2["transport_repo"], scenario) + _pick(WIT_UO2["geologic_disp"], scenario)
    else:
        raise ValueError(f"Unknown pellet_material: {d.pellet_material}")

    # Avoid double counting: split fab into process vs embedded hardware
    hs = max(0.0, min(0.9, float(hardware_share_in_toll)))
    c_fab_process = (1.0 - hs) * c_fab_total

    # Procurement = front-end + fabrication(process part) + hardware
    procurement_total = d.num_rods * (mHM_rod * (c_front + c_fab_process)) + C_hw_total
    backend_total = d.num_rods * (mHM_rod * c_backend) if include_backend else 0.0
    lifecycle_total = procurement_total + backend_total

    # ---------- Burnup lifetime ----------
    # E_th(kWh) = burnup(GWd/t) * mHM(t) * 24(GWh/GWd) * 1e6(kWh/GWh)
    mHM_t = mHM_total / 1000.0
    E_th_kWh = burnup * mHM_t * 24.0 * 1_000_000.0
    annual_kWh = P_core_kW * float(capacity_factor) * 8760.0
    rod_interval_years = max(0.25, E_th_kWh / max(1.0, annual_kWh))

    # ---------- Annual costs (transparent proxies) ----------
    annualized_replacement = procurement_total / rod_interval_years
    operational_per_year = (float(fixed_ops_per_year_usd) + annualized_replacement) * smr["ops_mult"]
    maintenance_per_year = 0.03 * procurement_total * smr["maint_mult"]
    risk_reserve_per_year = 0.00  # keep 0 unless you add a user knob

    # Normalized outputs (compare fuels fairly)
    E_th_MWh_per_rod = (E_th_kWh / max(1, d.num_rods)) / 1000.0
    procurement_per_rod = procurement_total / max(1, d.num_rods)
    lifecycle_per_rod = lifecycle_total / max(1, d.num_rods)

    # ---------- $/MWh metrics ----------
    thermal_to_electric_eff = 0.33

    procurement_per_MWh_th = procurement_per_rod / max(1e-9, E_th_MWh_per_rod)
    lifecycle_per_MWh_th = lifecycle_per_rod / max(1e-9, E_th_MWh_per_rod)

    procurement_per_MWh_e = procurement_per_MWh_th / thermal_to_electric_eff
    lifecycle_per_MWh_e = lifecycle_per_MWh_th / thermal_to_electric_eff

    return {
        "core_power_MWt": core_power_MWt_out,
        "num_rods": d.num_rods,
        "installation_cost": procurement_total,
        "lifecycle_total_cost": lifecycle_total,
        "operational_cost_per_year": operational_per_year,
        "maintenance_cost_per_year": maintenance_per_year,
        "risk_reserve_per_year": risk_reserve_per_year,
        "rod_change_interval_years": rod_interval_years,
        "normalized": {
            "mHM_kg_per_rod": mHM_rod,
            "E_th_MWh_per_rod": E_th_MWh_per_rod,
            "procurement_cost_per_rod": procurement_per_rod,
            "lifecycle_cost_per_rod": lifecycle_per_rod,

            "procurement_$per_MWh_th": procurement_per_MWh_th,
            "lifecycle_$per_MWh_th": lifecycle_per_MWh_th,

            "procurement_$per_MWh_e": procurement_per_MWh_e,
            "lifecycle_$per_MWh_e": lifecycle_per_MWh_e,
        },
        "debug": {
            "qprime_kW_per_m_assumed": qprime,
            "burnup_GWd_tHM": burnup,
            "m_clad_kg_per_rod": m_clad,
            "hardware_cost_per_rod": C_hw_rod,
            "hardware_cost_total": C_hw_total,
            "c_front_$perkg": c_front,
            "c_fab_total_$perkg": c_fab_total,
            "c_fab_process_$perkg": c_fab_process,
            "c_backend_$perkg": c_backend,
            "hardware_share_in_toll": hs,
        }
    }