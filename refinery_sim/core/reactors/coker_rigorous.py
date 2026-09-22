"""Coker furnace + drum rigorous sequence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..components import Stream
from ..units import CokerParams, delayed_coker


@dataclass
class CokerRigorousResult:
    products: Dict[str, Stream]
    furnace_duty_mw: float
    coke_in_drum_mt_h: float
    diagnostics: Dict[str, Any]


def coker_rigorous_train(
    feed: Stream,
    furnace_params: Dict[str, float],
    drum_params: Dict[str, float],
    decoke_params: Dict[str, float] | None = None,
) -> CokerRigorousResult:
    outlet_c = float(furnace_params.get("outlet_c", 495))
    soak = float(furnace_params.get("residence_time_min", 2.5))
    drum_p = float(drum_params.get("drum_pressure_kpa", 35))
    fill = float(drum_params.get("cycle_fill_frac", 0.85))

    feed_mass = feed.flows.get("vac_residue", 0.0) + 0.5 * feed.total()
    # Higher furnace outlet → more conversion, slightly less coke
    coke_y = 0.32 - 0.0002 * (outlet_c - 480) + 0.02 * (1.0 - fill)
    coke_y = max(0.22, min(0.35, coke_y))

    coker_p = CokerParams(drum_pressure_kpa=drum_p, coke_yield_wt=coke_y)
    products = delayed_coker(feed, coker_p)

    furnace_duty = feed_mass * 2.8 * (outlet_c - 200.0) / 3600.0  # MW anchor
    coke_mt = products["coke"].flows.get("coke", feed_mass * coke_y)

    dp = decoke_params or {}
    steam_cycle = float(dp.get("steam_mt_per_cycle", 120))

    return CokerRigorousResult(
        products=products,
        furnace_duty_mw=furnace_duty,
        coke_in_drum_mt_h=coke_mt,
        diagnostics={
            "furnace_outlet_c": outlet_c,
            "soak_min": soak,
            "drum_pressure_kpa": drum_p,
            "decoking_steam_mt_per_cycle": steam_cycle,
        },
    )
