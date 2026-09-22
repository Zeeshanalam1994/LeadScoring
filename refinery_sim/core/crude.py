"""Crude assay and atmospheric distillation (CDU) first-principles split."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .components import COMPONENTS, Stream


@dataclass
class CrudeAssay:
    """
    Whole-crude mass yields (fraction of crude) by pseudo-component.
    Values should sum to ~1.0 for hydrocarbon lumps; light ends may be embedded.
    """

    name: str
    api: float
    sulfur_wt_pct: float
    yields: Dict[str, float]

    def normalized_yields(self) -> Dict[str, float]:
        total = sum(self.yields.get(c, 0.0) for c in COMPONENTS if c not in ("coke", "hydrogen"))
        if total <= 0:
            raise ValueError("Crude assay yields must be positive")
        return {c: self.yields.get(c, 0.0) / total for c in COMPONENTS if c not in ("coke", "hydrogen")}


# Reference medium sour crude (typical Middle East–type slate, mass basis).
BENCHMARK_CRUDE = CrudeAssay(
    name="Arabian Medium",
    api=31.0,
    sulfur_wt_pct=2.5,
    yields={
        "light_gas": 0.015,
        "lpg": 0.025,
        "naphtha": 0.18,
        "kerosene": 0.11,
        "diesel": 0.22,
        "gas_oil": 0.28,
        "vac_residue": 0.17,
        "coke": 0.0,
        "hydrogen": 0.0,
    },
)


def crude_feed_stream(rate_mt_h: float, assay: CrudeAssay) -> Stream:
    y = assay.normalized_yields()
    s = Stream(name=f"crude_{assay.name}")
    for c, frac in y.items():
        s.flows[c] = rate_mt_h * frac
    return s


@dataclass
class CDUCutPoints:
    """Atmospheric cut temperatures (°C, 1 atm equivalent)."""

    naphtha_end: float = 180.0
    kerosene_end: float = 250.0
    diesel_end: float = 350.0
    gas_oil_end: float = 565.0


def cdu_split(feed: Stream, cuts: CDUCutPoints, recovery_eff: float = 0.995) -> Dict[str, Stream]:
    """
    Atmospheric distillation — seven product streams:
    offgas, lpg, naphtha, kerosene, diesel, ago (atm gas oil), bottoms (atm residue).
    """
    total_in = feed.total()
    empty = {
        "offgas": Stream(name="cdu_offgas"),
        "lpg": Stream(name="cdu_lpg"),
        "naphtha": Stream(name="cdu_naphtha"),
        "kerosene": Stream(name="cdu_kerosene"),
        "diesel": Stream(name="cdu_diesel"),
        "ago": Stream(name="cdu_ago"),
        "bottoms": Stream(name="cdu_bottoms"),
    }
    if total_in <= 0:
        return empty

    offgas = Stream(name="cdu_offgas")
    lpg = Stream(name="cdu_lpg")
    naphtha = Stream(name="cdu_naphtha")
    kero = Stream(name="cdu_kerosene")
    diesel = Stream(name="cdu_diesel")
    ago = Stream(name="cdu_ago")
    bottoms = Stream(name="cdu_bottoms")

    for comp, rate in feed.flows.items():
        if comp in ("coke", "hydrogen") or rate <= 0:
            continue
        if comp == "light_gas":
            offgas.flows["light_gas"] += rate
        elif comp == "lpg":
            lpg.flows["lpg"] += rate
        elif comp == "naphtha":
            naphtha.flows["naphtha"] += rate
        elif comp == "kerosene":
            kero.flows["kerosene"] += rate
        elif comp == "diesel":
            diesel.flows["diesel"] += rate
        elif comp == "gas_oil":
            ago.flows["gas_oil"] += rate * 0.88
            bottoms.flows["gas_oil"] += rate * 0.12
        elif comp == "vac_residue":
            bottoms.flows["vac_residue"] += rate

    product_streams = [offgas, lpg, naphtha, kero, diesel, ago, bottoms]
    scale = recovery_eff * total_in / max(sum(s.total() for s in product_streams), 1e-9)
    for s in product_streams:
        for c in s.flows:
            s.flows[c] *= scale

    return {
        "offgas": offgas,
        "lpg": lpg,
        "naphtha": naphtha,
        "kerosene": kero,
        "diesel": diesel,
        "ago": ago,
        "bottoms": bottoms,
    }
