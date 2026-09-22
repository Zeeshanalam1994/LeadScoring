"""Process unit models — yield correlations with closed mass balances."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .components import Stream, empty_stream


@dataclass
class VDUParams:
    flash_pressure_kpa: float = 5.0
    heater_outlet_c: float = 400.0
    vgo_yield_wt: float = 0.55  # VGO on VR feed
    vr_yield_wt: float = 0.43
    gas_yield_wt: float = 0.02


def vdu_split(feed: Stream, p: VDUParams) -> Dict[str, Stream]:
    """Vacuum distillation — offgas, lpg (lights), VGO, vacuum bottoms."""
    feed_mass = feed.total()
    if feed_mass <= 0:
        return {
            "offgas": empty_stream("vdu_offgas"),
            "lpg": empty_stream("vdu_lpg"),
            "vgo": empty_stream("vdu_vgo"),
            "bottoms": empty_stream("vdu_bottoms"),
        }

    total_y = p.vgo_yield_wt + p.vr_yield_wt + p.gas_yield_wt
    vgo_f = p.vgo_yield_wt / total_y
    vr_f = p.vr_yield_wt / total_y
    gas_f = p.gas_yield_wt / total_y

    vgo = Stream(name="vdu_vgo")
    vr = Stream(name="vdu_bottoms")
    gas = Stream(name="vdu_offgas")
    lpg = Stream(name="vdu_lpg")

    for c, m in feed.flows.items():
        if c in ("coke", "hydrogen") or m <= 0:
            continue
        vgo.flows["gas_oil"] += m * vgo_f * (1.0 if c in ("gas_oil", "vac_residue", "diesel") else 0.15)
        vgo.flows[c] += m * vgo_f * (0.85 if c not in ("gas_oil", "vac_residue") else 0.0)
        vr.flows["vac_residue"] += m * vr_f * (1.0 if c in ("vac_residue", "gas_oil") else 0.2)
        vr.flows[c] += m * vr_f * (0.8 if c == "diesel" else 0.0)
        gas.flows["light_gas"] += m * gas_f * 0.55
        lpg.flows["lpg"] += m * gas_f * 0.45

    _close_balance(feed_mass, [vgo, vr, gas, lpg])
    return {"offgas": gas, "lpg": lpg, "vgo": vgo, "bottoms": vr}


@dataclass
class FCCParams:
    reactor_temp_c: float = 520.0
    cat_oil_ratio: float = 5.5
    conversion_wt: float = 0.75  # VGO to lighter products
    coke_make_wt: float = 0.06  # on feed


def fcc_reactor(feed: Stream, p: FCCParams) -> Dict[str, Stream]:
    """
    Fluid catalytic cracking — lumped yield matrix (Gary & Handwerk / Ritter correlations).
    Feed: predominantly gas_oil (VGO).
    """
    feed_mass = feed.flows.get("gas_oil", 0.0) + 0.3 * feed.total()
    if feed_mass <= 0:
        return {
            "lpg": empty_stream("fcc_lpg"),
            "gasoline": empty_stream("fcc_gasoline"),
            "lco": empty_stream("fcc_lco"),
            "offgas": empty_stream("fcc_gas"),
            "coke": empty_stream("fcc_coke"),
        }

    conv = max(0.05, min(0.92, p.conversion_wt))
    # Product yields (wt% of VGO feed) at given conversion.
    gasoline_y = 0.22 + 0.48 * conv
    lpg_y = 0.08 + 0.12 * conv
    gas_y = 0.05 + 0.08 * conv
    lco_y = max(0.05, 0.55 - 0.45 * conv)
    coke_y = p.coke_make_wt

    lpg = Stream(name="fcc_lpg")
    gasoline = Stream(name="fcc_gasoline")
    lco = Stream(name="fcc_lco")
    gas = Stream(name="fcc_offgas")
    coke = Stream(name="fcc_coke")

    lpg.flows["lpg"] = feed_mass * lpg_y
    gasoline.flows["naphtha"] = feed_mass * gasoline_y * 0.85
    gasoline.flows["light_gas"] = feed_mass * gasoline_y * 0.15
    lco.flows["gas_oil"] = feed_mass * lco_y
    lco.flows["diesel"] = feed_mass * lco_y * 0.15
    gas.flows["light_gas"] = feed_mass * gas_y * 0.6
    gas.flows["lpg"] = feed_mass * gas_y * 0.4
    coke.flows["coke"] = feed_mass * coke_y

    _close_balance(feed_mass, [lpg, gasoline, lco, gas, coke])
    return {"lpg": lpg, "gasoline": gasoline, "lco": lco, "offgas": gas, "coke": coke}


@dataclass
class HydrocrackerParams:
    reactor_pressure_mpa: float = 15.0
    lhsv: float = 1.2
    conversion_wt: float = 0.85
    h2_consumption_wt: float = 0.025  # wt H2 per wt feed


def hydrocracker(feed: Stream, p: HydrocrackerParams) -> Dict[str, Stream]:
    """Hydrocracking — hydrogen addition, saturation, cracking to middle distillates."""
    feed_mass = feed.flows.get("gas_oil", 0.0) + 0.25 * feed.total()
    if feed_mass <= 0:
        return {
            "offgas": empty_stream("hc_offgas"),
            "lpg": empty_stream("hc_lpg"),
            "naphtha": empty_stream("hc_naphtha"),
            "kerosene": empty_stream("hc_kero"),
            "diesel": empty_stream("hc_diesel"),
            "unconverted": empty_stream("hc_uco"),
        }

    conv = max(0.1, min(0.98, p.conversion_wt))
    naph_y = 0.08 + 0.25 * conv
    kero_y = 0.15 + 0.20 * conv
    diesel_y = 0.35 + 0.15 * (1.0 - conv)
    gas_y = 0.05 + 0.10 * conv
    h2_net = -feed_mass * p.h2_consumption_wt

    naphtha = Stream(name="hc_naphtha")
    kero = Stream(name="hc_kerosene")
    diesel = Stream(name="hc_diesel")
    gas = Stream(name="hc_offgas")

    naphtha.flows["naphtha"] = feed_mass * naph_y
    kero.flows["kerosene"] = feed_mass * kero_y
    diesel.flows["diesel"] = feed_mass * diesel_y
    gas.flows["light_gas"] = feed_mass * gas_y * 0.5
    gas.flows["lpg"] = feed_mass * gas_y * 0.5
    gas.flows["hydrogen"] = h2_net

    # Mass gain from H2 (first principles: hydrogen incorporation).
    h2_added = feed_mass * p.h2_consumption_wt
    diesel.flows["diesel"] += h2_added * 0.6
    kero.flows["kerosene"] += h2_added * 0.4

    lpg = Stream(name="hc_lpg")
    lpg.flows["lpg"] = gas.flows.get("lpg", 0.0)
    gas.flows["lpg"] = 0.0
    unconverted = Stream(name="hc_uco")
    unconverted.flows["gas_oil"] = feed_mass * (1.0 - conv) * 0.85

    _close_balance(feed_mass + h2_added, [naphtha, kero, diesel, gas, lpg, unconverted], ignore_h2=True)
    return {
        "offgas": gas,
        "lpg": lpg,
        "naphtha": naphtha,
        "kerosene": kero,
        "diesel": diesel,
        "unconverted": unconverted,
    }


@dataclass
class CokerParams:
    drum_pressure_kpa: float = 35.0
    cycle_hours: float = 24.0
    coke_yield_wt: float = 0.28
    conversion_wt: float = 0.65


def delayed_coker(feed: Stream, p: CokerParams) -> Dict[str, Stream]:
    """Delayed coking — thermal cracking of vacuum residue."""
    feed_mass = feed.flows.get("vac_residue", 0.0) + 0.5 * feed.total()
    if feed_mass <= 0:
        return {
            "lpg": empty_stream("coker_lpg"),
            "naphtha": empty_stream("coker_naphtha"),
            "lco": empty_stream("coker_lco"),
            "coke": empty_stream("coker_coke"),
            "offgas": empty_stream("coker_gas"),
        }

    coke_y = p.coke_yield_wt
    gas_y = 0.08
    lpg_y = 0.05
    naph_y = 0.12
    lco_y = max(0.05, 1.0 - coke_y - gas_y - lpg_y - naph_y)

    lpg = Stream(name="coker_lpg")
    naphtha = Stream(name="coker_naphtha")
    lco = Stream(name="coker_lco")
    coke = Stream(name="coker_coke")
    gas = Stream(name="coker_gas")

    lpg.flows["lpg"] = feed_mass * lpg_y
    naphtha.flows["naphtha"] = feed_mass * naph_y
    lco.flows["gas_oil"] = feed_mass * lco_y * 0.7
    lco.flows["diesel"] = feed_mass * lco_y * 0.3
    coke.flows["coke"] = feed_mass * coke_y
    gas.flows["light_gas"] = feed_mass * gas_y

    _close_balance(feed_mass, [lpg, naphtha, lco, coke, gas])
    return {"lpg": lpg, "naphtha": naphtha, "lco": lco, "coke": coke, "offgas": gas}


@dataclass
class CCRParams:
    reactor_pressure_mpa: float = 2.5
    wait: float = 6.0  # WABT index placeholder
    reformate_yield_wt: float = 0.82
    h2_yield_wt: float = 0.03  # wt H2 per wt naphtha feed


def ccr_reformer(feed: Stream, p: CCRParams) -> Dict[str, Stream]:
    """Continuous catalytic reforming — dehydrocyclization / isomerization."""
    feed_mass = feed.flows.get("naphtha", 0.0) + 0.1 * feed.flows.get("light_gas", 0.0)
    if feed_mass <= 0:
        return {
            "offgas": empty_stream("ccr_offgas"),
            "lpg": empty_stream("ccr_lpg"),
            "reformate": empty_stream("ccr_reformate"),
            "h2": empty_stream("ccr_h2"),
        }

    ref_y = p.reformate_yield_wt
    gas_y = 1.0 - ref_y - p.h2_yield_wt

    reformate = Stream(name="ccr_reformate")
    offgas = Stream(name="ccr_offgas")
    h2 = Stream(name="ccr_h2")

    reformate.flows["naphtha"] = feed_mass * ref_y * 0.9
    reformate.flows["light_gas"] = feed_mass * ref_y * 0.1
    offgas.flows["light_gas"] = feed_mass * gas_y * 0.7
    offgas.flows["lpg"] = feed_mass * gas_y * 0.3
    h2.flows["hydrogen"] = feed_mass * p.h2_yield_wt

    lpg = Stream(name="ccr_lpg")
    lpg.flows["lpg"] = offgas.flows.get("lpg", 0.0)
    offgas.flows["lpg"] = 0.0

    _close_balance(feed_mass, [reformate, offgas, lpg, h2], ignore_h2=True)
    return {"offgas": offgas, "lpg": lpg, "reformate": reformate, "h2": h2}


def _close_balance(feed_mass: float, products: list[Stream], ignore_h2: bool = False) -> None:
    """Scale product hydrocarbon flows to match feed mass (closure)."""
    total = sum(s.total() for s in products)
    if total <= 0:
        return
    target = feed_mass
    if ignore_h2:
        h2_sum = sum(s.flows.get("hydrogen", 0.0) for s in products)
        target = feed_mass - max(0.0, h2_sum)
    scale = target / total
    if abs(scale - 1.0) < 1e-6:
        return
    for s in products:
        for c in s.flows:
            if ignore_h2 and c == "hydrogen":
                continue
            s.flows[c] *= scale
