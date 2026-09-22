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


def _cumulative_cut_fractions(assay: CrudeAssay, cuts: CDUCutPoints) -> Tuple[float, float, float, float]:
    """
    Map boiling-range cuts to pseudo-component splits using assay shape.
    Assumes monotonic TBP-like distribution within each lump (trapezoidal split).
    """
    y = assay.normalized_yields()
    # Represent each lump by mid boiling point (°C) for interpolation.
    mid = {
        "light_gas": 20.0,
        "lpg": 80.0,
        "naphtha": 120.0,
        "kerosene": 215.0,
        "diesel": 300.0,
        "gas_oil": 450.0,
        "vac_residue": 620.0,
    }
    boundaries = [0.0, cuts.naphtha_end, cuts.kerosene_end, cuts.diesel_end, cuts.gas_oil_end, 800.0]
    bucket_names = ["light_ends", "naphtha_cut", "kero_cut", "diesel_cut", "gas_oil_cut", "atm_residue"]

    buckets = {b: 0.0 for b in bucket_names}
    for comp, frac in y.items():
        if comp in ("coke", "hydrogen", "vac_residue"):
            continue
        t = mid[comp]
        # Assign lump mass to atmospheric buckets by overlap with cut intervals.
        for i in range(len(boundaries) - 1):
            lo, hi = boundaries[i], boundaries[i + 1]
            if t <= lo:
                continue
            if t >= hi:
                if i == len(boundaries) - 2:
                    buckets[bucket_names[i]] += frac
                continue
            # Partial assignment: use uniform distribution within pseudo-lump width.
            lump_lo = mid[comp] - 40 if comp != "light_gas" else 0
            lump_hi = mid[comp] + 40 if comp != "vac_residue" else 700
            overlap = max(0.0, min(hi, lump_hi) - max(lo, lump_lo))
            width = max(lump_hi - lump_lo, 1.0)
            buckets[bucket_names[i]] += frac * (overlap / width)

    # Residue from crude assay + anything above gas_oil_end.
    buckets["atm_residue"] += y.get("vac_residue", 0.0)
    return (
        buckets["light_ends"] + buckets["naphtha_cut"] * 0.3,
        buckets["naphtha_cut"] * 0.7 + buckets["kero_cut"],
        buckets["diesel_cut"],
        buckets["gas_oil_cut"],
        buckets["atm_residue"],
    )


def cdu_split(feed: Stream, cuts: CDUCutPoints, recovery_eff: float = 0.995) -> Dict[str, Stream]:
    """
    Atmospheric distillation: partition feed pseudo-components into product cuts.
    Mass balance: sum(outputs) = recovery_eff * feed (light loss to VR).
    """
    total_in = feed.total()
    if total_in <= 0:
        return {
            "offgas_lpg": Stream(name="cdu_offgas"),
            "naphtha": Stream(name="cdu_naphtha"),
            "kerosene": Stream(name="cdu_kerosene"),
            "diesel": Stream(name="cdu_diesel"),
            "atm_residue": Stream(name="cdu_residue"),
        }

    # Proportional split by component type (first principles on boiling range).
    offgas = Stream(name="cdu_offgas")
    naphtha = Stream(name="cdu_naphtha")
    kero = Stream(name="cdu_kerosene")
    diesel = Stream(name="cdu_diesel")
    residue = Stream(name="cdu_residue")

    split_map = {
        "light_gas": ("offgas", 1.0),
        "lpg": ("offgas", 1.0),
        "naphtha": ("naphtha", 1.0),
        "kerosene": ("kero", 1.0),
        "diesel": ("diesel", 1.0),
        "gas_oil": ("residue", 0.15),  # partial overlap to residue in atm column
        "vac_residue": ("residue", 1.0),
    }
    targets = {"offgas": offgas, "naphtha": naphtha, "kero": kero, "diesel": diesel, "residue": residue}

    for comp, rate in feed.flows.items():
        if comp in ("coke", "hydrogen") or rate <= 0:
            continue
        key, frac = split_map.get(comp, ("residue", 1.0))
        targets[key].flows[comp] += rate * frac
        if comp == "gas_oil":
            residue.flows[comp] += rate * (1.0 - frac)

    scale = recovery_eff * total_in / max(
        offgas.total() + naphtha.total() + kero.total() + diesel.total() + residue.total(), 1e-9
    )
    for s in (offgas, naphtha, kero, diesel, residue):
        for c in s.flows:
            s.flows[c] *= scale

    return {
        "offgas_lpg": offgas,
        "naphtha": naphtha,
        "kerosene": kero,
        "diesel": diesel,
        "atm_residue": residue,
    }
