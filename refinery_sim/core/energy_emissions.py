"""Plant-wide steam and emissions aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .heaters import HeaterResult
from .schema import UnitId


# Typical steam demand (MT/h) per MT/h feed at reference throughput — first-principles anchor values.
STEAM_CONSUMPTION_MT_PER_MT_FEED: Dict[UnitId, float] = {
    "CDU": 0.012,
    "VDU": 0.008,
    "FCC": 0.025,
    "HYDROCRACKER": 0.018,
    "COKER": 0.015,
    "CCR": 0.010,
}


@dataclass
class EnergyBalance:
    total_duty_mw: float
    total_fuel_mt_h: float
    steam_generated_mt_h: float
    steam_consumed_mt_h: float
    net_steam_mt_h: float
    specific_energy_gj_per_mt_crude: float
    electricity_equivalent_mw: float


@dataclass
class EmissionsBalance:
    co2_fuel_mt_h: float
    co2_flare_mt_h: float
    co2_total_mt_h: float
    so2_kg_h: float
    nox_kg_h: float
    co2_specific_kg_per_mt_crude: float


def aggregate_energy(
    heaters: List[HeaterResult],
    unit_feed_mt_h: Dict[UnitId, float],
    crude_mt_h: float,
) -> EnergyBalance:
    duty = sum(h.duty_mw for h in heaters)
    fuel = sum(h.fuel_mt_h for h in heaters)
    steam_gen = sum(h.steam_generated_mt_h for h in heaters)
    steam_cons = 0.0
    for uid, sf in STEAM_CONSUMPTION_MT_PER_MT_FEED.items():
        steam_cons += unit_feed_mt_h.get(uid, 0.0) * sf
    # FCC regenerator air blower / pumps — anchor
    steam_cons += unit_feed_mt_h.get("FCC", 0.0) * 0.01
    net_steam = steam_gen - steam_cons
    gj_h = duty * 3.6 + fuel * 42.0
    spec = gj_h / crude_mt_h if crude_mt_h > 0 else 0.0
    elec_mw = duty * 0.05  # driver power ~5% of fired duty
    return EnergyBalance(
        total_duty_mw=duty,
        total_fuel_mt_h=fuel,
        steam_generated_mt_h=steam_gen,
        steam_consumed_mt_h=steam_cons,
        net_steam_mt_h=net_steam,
        specific_energy_gj_per_mt_crude=spec,
        electricity_equivalent_mw=elec_mw,
    )


def aggregate_emissions(
    heaters: List[HeaterResult],
    flare_gas_mt_h: float,
    crude_mt_h: float,
) -> EmissionsBalance:
    co2_fuel = sum(h.co2_mt_h for h in heaters)
    # Flare gas — predominantly CH4/C3, ~2.75 kg CO2 per kg gas equivalent
    co2_flare = flare_gas_mt_h * 2.75
    so2 = sum(h.so2_kg_h for h in heaters)
    nox = sum(h.nox_kg_h for h in heaters)
    total_co2 = co2_fuel + co2_flare
    spec = (total_co2 * 1000.0) / crude_mt_h if crude_mt_h > 0 else 0.0
    return EmissionsBalance(
        co2_fuel_mt_h=co2_fuel,
        co2_flare_mt_h=co2_flare,
        co2_total_mt_h=total_co2,
        so2_kg_h=so2,
        nox_kg_h=nox,
        co2_specific_kg_per_mt_crude=spec,
    )
