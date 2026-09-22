"""Crude feeders and assay blending."""

from __future__ import annotations

from typing import Dict, List, Tuple

from .crude import BENCHMARK_CRUDE, CrudeAssay, crude_feed_stream
from .components import Stream
from .properties import StreamProperties, api_to_density, blend_properties


def assay_from_record(record: dict) -> CrudeAssay:
    return CrudeAssay(
        name=record["name"],
        api=float(record["api"]),
        sulfur_wt_pct=float(record["sulfur_wt_pct"]),
        yields=dict(record["yields"]),
    )


def blend_assays(
    assays: Dict[str, CrudeAssay],
    components: List[Tuple[str, float]],
) -> Tuple[CrudeAssay, StreamProperties]:
    """
    Blend multiple crudes by mass rate (MT/h).
    Yields and bulk properties are mass-weighted.
    """
    total_rate = sum(r for _, r in components if r > 0)
    if total_rate <= 0:
        raise ValueError("Feeder blend requires positive total crude rate")

    yield_acc: Dict[str, float] = {}
    prop_items: List[Tuple[float, StreamProperties]] = []

    for assay_id, rate in components:
        if rate <= 0:
            continue
        assay = assays.get(assay_id)
        if assay is None:
            raise ValueError(f"Unknown assay id: {assay_id}")
        y = assay.normalized_yields()
        for k, v in y.items():
            yield_acc[k] = yield_acc.get(k, 0.0) + v * rate
        prop_items.append(
            (
                rate,
                StreamProperties(
                    sulfur_wt_pct=assay.sulfur_wt_pct,
                    density_kg_m3=api_to_density(assay.api),
                    api=assay.api,
                    lhv_mj_kg=42.0,
                ),
            )
        )

    blended_yields = {k: v / total_rate for k, v in yield_acc.items()}
    props = blend_properties(prop_items)
    names = [assays[c[0]].name for c in components if c[1] > 0]
    blended = CrudeAssay(
        name="Blend(" + "+".join(names[:3]) + ("..." if len(names) > 3 else "") + ")",
        api=props.api,
        sulfur_wt_pct=props.sulfur_wt_pct,
        yields=blended_yields,
    )
    return blended, props


def build_crude_charge(
    assays: Dict[str, CrudeAssay],
    components: List[Tuple[str, float]],
) -> Tuple[Stream, CrudeAssay, StreamProperties, float]:
    blended, props = blend_assays(assays, components)
    total_rate = sum(r for _, r in components)
    stream = crude_feed_stream(total_rate, blended)
    stream.name = "blended_crude"
    return stream, blended, props, total_rate


def default_assay_library() -> Dict[str, CrudeAssay]:
    light = CrudeAssay(
        name="Light Sweet",
        api=38.0,
        sulfur_wt_pct=0.4,
        yields={
            "light_gas": 0.02,
            "lpg": 0.04,
            "naphtha": 0.26,
            "kerosene": 0.14,
            "diesel": 0.24,
            "gas_oil": 0.22,
            "vac_residue": 0.08,
            "coke": 0.0,
            "hydrogen": 0.0,
        },
    )
    heavy = CrudeAssay(
        name="Heavy Sour",
        api=22.0,
        sulfur_wt_pct=3.8,
        yields={
            "light_gas": 0.01,
            "lpg": 0.02,
            "naphtha": 0.10,
            "kerosene": 0.08,
            "diesel": 0.18,
            "gas_oil": 0.26,
            "vac_residue": 0.35,
            "coke": 0.0,
            "hydrogen": 0.0,
        },
    )
    return {
        "arab_medium": BENCHMARK_CRUDE,
        "light_sweet": light,
        "heavy_sour": heavy,
    }
