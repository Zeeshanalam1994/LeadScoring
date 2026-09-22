"""Fired heater and heat-integration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .schema import UnitId


@dataclass
class HeaterModel:
    id: str
    unit_id: UnitId
    name: str
    inlet_c: float
    outlet_c: float
    cp_kj_kg_k: float = 2.4
    thermal_efficiency: float = 0.92
    fuel_lhv_mj_kg: float = 45.0  # fuel gas
    carbon_wt_frac: float = 0.75
    sulfur_wt_frac_fuel: float = 0.001
    steam_generation_frac: float = 0.0  # fraction of duty to HP steam


@dataclass
class HeaterResult:
    id: str
    unit_id: UnitId
    name: str
    feed_mt_h: float
    duty_mw: float
    fuel_mt_h: float
    steam_generated_mt_h: float
    co2_mt_h: float
    so2_kg_h: float
    nox_kg_h: float


def heater_duty_mw(feed_mt_h: float, cp_kj_kg_k: float, inlet_c: float, outlet_c: float) -> float:
    """Q = m * Cp * ΔT ; m in kg/s from MT/h."""
    if feed_mt_h <= 0 or outlet_c <= inlet_c:
        return 0.0
    m_kg_s = feed_mt_h * 1000.0 / 3600.0
    q_kw = m_kg_s * cp_kj_kg_k * (outlet_c - inlet_c)
    return q_kw / 1000.0


def simulate_heater(heater: HeaterModel, feed_mt_h: float) -> HeaterResult:
    duty = heater_duty_mw(feed_mt_h, heater.cp_kj_kg_k, heater.inlet_c, heater.outlet_c)
    fuel_energy_mw = duty / max(heater.thermal_efficiency, 0.1)
    fuel_mt_h = fuel_energy_mw * 3600.0 / (heater.fuel_lhv_mj_kg * 1000.0) if heater.fuel_lhv_mj_kg > 0 else 0.0
    steam_mt_h = duty * heater.steam_generation_frac * 0.18  # empirical t steam per MW-h
    co2 = fuel_mt_h * heater.carbon_wt_frac * (44.0 / 12.0)
    so2_kg = fuel_mt_h * heater.sulfur_wt_frac_fuel * 1000.0 * 2.0
    nox_kg = duty * 0.45  # kg/h ~0.45 kg/MW (turbulent fired heater order of magnitude)
    return HeaterResult(
        id=heater.id,
        unit_id=heater.unit_id,
        name=heater.name,
        feed_mt_h=feed_mt_h,
        duty_mw=duty,
        fuel_mt_h=fuel_mt_h,
        steam_generated_mt_h=steam_mt_h,
        co2_mt_h=co2,
        so2_kg_h=so2_kg,
        nox_kg_h=nox_kg,
    )


def default_heater_map() -> Dict[UnitId, HeaterModel]:
    return {
        "CDU": HeaterModel("h_cdu", "CDU", "Crude furnace", 120, 365, cp_kj_kg_k=2.5, steam_generation_frac=0.05),
        "VDU": HeaterModel("h_vdu", "VDU", "Vacuum heater", 280, 405, cp_kj_kg_k=2.35, steam_generation_frac=0.02),
        "FCC": HeaterModel("h_fcc", "FCC", "FCC charge heater", 180, 315, cp_kj_kg_k=2.3, steam_generation_frac=0.0),
        "HYDROCRACKER": HeaterModel(
            "h_hc", "HYDROCRACKER", "HC feed heater", 150, 385, cp_kj_kg_k=2.4, steam_generation_frac=0.0
        ),
        "COKER": HeaterModel("h_coker", "COKER", "Coker furnace", 200, 495, cp_kj_kg_k=2.2, steam_generation_frac=0.08),
        "CCR": HeaterModel("h_ccr", "CCR", "Reformer heaters", 110, 520, cp_kj_kg_k=2.6, steam_generation_frac=0.03),
    }
