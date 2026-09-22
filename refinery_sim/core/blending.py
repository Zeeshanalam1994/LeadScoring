"""Product blenders with specification checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .properties import PoolAccumulator, StreamProperties, blend_properties


@dataclass
class BlenderSource:
    pool: str
    tag: str  # logical substream within pool (e.g. fcc, ccr, straight_run)
    fraction_of_pool: float  # 0-1 of that pool+tag inventory


@dataclass
class BlenderSpecs:
    min_ron: Optional[float] = None
    max_ron: Optional[float] = None
    min_cetane: Optional[float] = None
    max_sulfur_wt_pct: Optional[float] = None
    min_density_kg_m3: Optional[float] = None
    max_density_kg_m3: Optional[float] = None


@dataclass
class BlenderDefinition:
    id: str
    name: str
    product: str
    sources: List[BlenderSource]
    specs: BlenderSpecs


@dataclass
class BlenderResult:
    blender_id: str
    name: str
    product: str
    rate_mt_h: float
    properties: Dict[str, float]
    specs_met: bool
    violations: List[str]


def run_blender(
    blender: BlenderDefinition,
    pool_tags: Dict[str, Dict[str, PoolAccumulator]],
) -> BlenderResult:
    """
    Pull configured fractions from tagged pool inventories and linear-blend properties.
    """
    items: List[Tuple[float, StreamProperties]] = []
    total = 0.0
    for src in blender.sources:
        pool = pool_tags.get(src.pool, {})
        acc = pool.get(src.tag)
        if acc is None or acc.mass_mt_h <= 0:
            continue
        pull = acc.mass_mt_h * max(0.0, min(1.0, src.fraction_of_pool))
        if pull <= 0:
            continue
        items.append((pull, acc.props))
        total += pull

    if total <= 0:
        return BlenderResult(
            blender_id=blender.id,
            name=blender.name,
            product=blender.product,
            rate_mt_h=0.0,
            properties={},
            specs_met=False,
            violations=["No material available for blend"],
        )

    props = blend_properties(items)
    violations: List[str] = []
    sp = blender.specs
    if sp.min_ron is not None and props.ron < sp.min_ron:
        violations.append(f"RON {props.ron:.1f} < min {sp.min_ron}")
    if sp.max_ron is not None and props.ron > sp.max_ron:
        violations.append(f"RON {props.ron:.1f} > max {sp.max_ron}")
    if sp.min_cetane is not None and props.cetane < sp.min_cetane:
        violations.append(f"Cetane {props.cetane:.1f} < min {sp.min_cetane}")
    if sp.max_sulfur_wt_pct is not None and props.sulfur_wt_pct > sp.max_sulfur_wt_pct:
        violations.append(f"Sulfur {props.sulfur_wt_pct:.3f}% > max {sp.max_sulfur_wt_pct}%")
    if sp.min_density_kg_m3 is not None and props.density_kg_m3 < sp.min_density_kg_m3:
        violations.append(f"Density {props.density_kg_m3:.0f} < min")
    if sp.max_density_kg_m3 is not None and props.density_kg_m3 > sp.max_density_kg_m3:
        violations.append(f"Density {props.density_kg_m3:.0f} > max")

    return BlenderResult(
        blender_id=blender.id,
        name=blender.name,
        product=blender.product,
        rate_mt_h=total,
        properties={
            "sulfur_wt_pct": props.sulfur_wt_pct,
            "density_kg_m3": props.density_kg_m3,
            "ron": props.ron,
            "cetane": props.cetane,
            "api": props.api,
        },
        specs_met=len(violations) == 0,
        violations=violations,
    )
