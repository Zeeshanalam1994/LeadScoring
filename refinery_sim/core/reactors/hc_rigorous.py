"""Rigorous hydrocracker trickle-bed + HP separator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..components import Stream
from ..units import HydrocrackerParams, hydrocracker


@dataclass
class HCRigorousResult:
    products: Dict[str, Stream]
    conversion_wt: float
    h2_partial_pressure_mpa: float
    reactor_duty_mw: float
    diagnostics: Dict[str, Any]


def hc_rigorous_train(
    feed: Stream,
    reactor_params: Dict[str, float],
    sep_params: Dict[str, float],
) -> HCRigorousResult:
    temp = float(reactor_params.get("reactor_temp_c", 385))
    p_tot = float(reactor_params.get("pressure_mpa", 15))
    lhsv = float(reactor_params.get("lhsv", 1.2))
    h2_oil = float(reactor_params.get("h2_oil_ratio", 650))  # Nm³/m³ approx scale

    feed_mass = feed.flows.get("gas_oil", 0.0) + 0.25 * feed.total()
    # Conversion correlation: higher T, P, lower LHSV → higher conversion
    conv = 0.55 + 0.002 * (temp - 350) + 0.012 * (p_tot - 10) - 0.08 * (lhsv - 1.0)
    conv += 0.00001 * h2_oil
    conv = max(0.35, min(0.98, conv))

    h2_pp = p_tot * min(0.85, 0.55 + h2_oil / 5000.0)

    hc_p = HydrocrackerParams(
        reactor_pressure_mpa=p_tot,
        lhsv=lhsv,
        conversion_wt=conv,
        h2_consumption_wt=0.018 + 0.01 * conv,
    )
    products = hydrocracker(feed, hc_p)

    sep_t = float(sep_params.get("separator_temp_c", 85))
    # Separator flashes light gas — small shift to offgas
    flash_frac = 0.02 + 0.0005 * (sep_t - 80)
    og = products["offgas"]
    og.flows["light_gas"] += feed_mass * flash_frac * 0.5

    reactor_duty = feed_mass * conv * 0.15 / 3.6  # exothermic anchor MW

    return HCRigorousResult(
        products=products,
        conversion_wt=conv,
        h2_partial_pressure_mpa=h2_pp,
        reactor_duty_mw=reactor_duty,
        diagnostics={"lhsv": lhsv, "separator_temp_c": sep_t},
    )
