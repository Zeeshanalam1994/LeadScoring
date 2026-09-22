"""Rigorous FCC riser + regenerator coupling (material, coke, and heat balance)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict

from ..components import Stream, empty_stream
from ..units import FCCParams, _close_balance


R_GAS = 8.314e-3  # kJ/mol/K
COKE_LHV_MJ_KG = 32.0
CRACKING_ENDOTHERM_MJ_KG = 0.42  # per kg VGO converted


@dataclass
class FCCRigorousResult:
    products: Dict[str, Stream]
    conversion_wt: float
    coke_to_regen_mt_h: float
    riser_duty_mw: float
    regen_duty_mw: float
    heat_balance_error_mw: float
    air_rate_mt_h: float
    flue_gas_mt_h: float
    cat_circulation_mt_h: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def _riser_conversion(temp_c: float, cat_oil: float, p: Dict[str, float]) -> float:
    """First-order riser cracking: X = 1 - exp(-k); k from Arrhenius and cat/oil."""
    a = float(p.get("preexponential", 2.5))
    ea = float(p.get("activation_kj_mol", 22.0))
    t_k = temp_c + 273.15
    k = a * (cat_oil / 5.5) * math.exp(-ea / (R_GAS * t_k))
    return max(0.05, min(0.92, 1.0 - math.exp(-k)))


def fcc_rigorous_train(
    feed: Stream,
    riser_params: Dict[str, float],
    regen_params: Dict[str, float],
    frac_params: Dict[str, float] | None = None,
) -> FCCRigorousResult:
    """
    Two-block FCC:
    1) Riser — kinetic conversion, product slate, coke on catalyst.
    2) Regenerator — coke burn, air, flue gas, heat release vs riser endotherm.
    Optional fractionator only adjusts gasoline/LCO split slightly.
    """
    feed_mass = feed.flows.get("gas_oil", 0.0) + 0.3 * feed.total()
    if feed_mass <= 0:
        empty = {
            "lpg": empty_stream("fcc_lpg"),
            "gasoline": empty_stream("fcc_gasoline"),
            "lco": empty_stream("fcc_lco"),
            "offgas": empty_stream("fcc_gas"),
            "coke": empty_stream("fcc_coke"),
            "flue_gas": empty_stream("fcc_flue"),
        }
        return FCCRigorousResult(
            products=empty,
            conversion_wt=0.0,
            coke_to_regen_mt_h=0.0,
            riser_duty_mw=0.0,
            regen_duty_mw=0.0,
            heat_balance_error_mw=0.0,
            air_rate_mt_h=0.0,
            flue_gas_mt_h=0.0,
            cat_circulation_mt_h=0.0,
        )

    riser_t = float(riser_params.get("riser_outlet_c", 520.0))
    cat_oil = float(riser_params.get("cat_oil_ratio", 5.5))
    conv = _riser_conversion(riser_t, cat_oil, riser_params)

    # Coke make increases with conversion and riser temperature.
    coke_y = 0.02 + 0.06 * conv + 0.00005 * (riser_t - 500.0) ** 2
    coke_y = max(0.03, min(0.12, coke_y))

    fcc_p = FCCParams(
        reactor_temp_c=riser_t,
        cat_oil_ratio=cat_oil,
        conversion_wt=conv,
        coke_make_wt=coke_y,
    )
    from ..units import fcc_reactor

    base = fcc_reactor(feed, fcc_p)

    # Fractionator: shift between gasoline and LCO.
    fp = frac_params or {}
    gas_bias = float(fp.get("gasoline_draw_frac", 0.48))
    shift = (gas_bias - 0.48) * feed_mass * 0.15
    base["gasoline"].flows["naphtha"] += shift
    base["lco"].flows["gas_oil"] -= shift * 0.8
    base["lco"].flows["diesel"] -= shift * 0.2

    coke_mt = feed_mass * coke_y
    base["coke"].flows["coke"] = coke_mt

    _close_balance(feed_mass, [base["lpg"], base["gasoline"], base["lco"], base["offgas"], base["coke"]])

    # --- Regenerator material & heat balance ---
    excess_air = float(regen_params.get("excess_air_frac", 0.15))
    cat_circ = float(regen_params.get("cat_circulation_mt_h", max(800.0, feed_mass * cat_oil)))
    # Stoichiometry: C + O2 -> CO2; O2 mass per coke ~ 32/12 * coke
    o2_required = coke_mt * (32.0 / 12.0)
    air_mt = o2_required / 0.23 * (1.0 + excess_air)
    flue = coke_mt * (44.0 / 12.0) + air_mt * 0.77  # N2 + excess O2 lumped with air

    regen_duty_mw = coke_mt * COKE_LHV_MJ_KG / 3.6
    riser_duty_mw = feed_mass * conv * CRACKING_ENDOTHERM_MJ_KG / 3.6
    # Catalyst sensible heat swing (anchor)
    regen_t = float(regen_params.get("regen_dense_bed_c", 715.0))
    cat_sensible = cat_circ * 1.1 * (regen_t - riser_t) / 3600.0  # MW ~ kJ/s
    heat_error = regen_duty_mw - riser_duty_mw - max(0.0, cat_sensible)

    flue_stream = Stream(name="fcc_flue_gas")
    flue_stream.flows["light_gas"] = flue * 0.9
    flue_stream.flows["coke"] = flue * 0.1  # carry as inert proxy

    base["flue_gas"] = flue_stream

    return FCCRigorousResult(
        products=base,
        conversion_wt=conv,
        coke_to_regen_mt_h=coke_mt,
        riser_duty_mw=riser_duty_mw,
        regen_duty_mw=regen_duty_mw,
        heat_balance_error_mw=heat_error,
        air_rate_mt_h=air_mt,
        flue_gas_mt_h=flue,
        cat_circulation_mt_h=cat_circ,
        diagnostics={
            "riser_outlet_c": riser_t,
            "cat_oil_ratio": cat_oil,
            "coke_yield_wt": coke_y,
            "regen_dense_bed_c": regen_t,
        },
    )
