"""Stream quality properties and linear blending rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class StreamProperties:
    """Bulk properties for linear blending (volume-linear where noted in refinery practice)."""

    sulfur_wt_pct: float = 0.0
    density_kg_m3: float = 850.0
    ron: float = 0.0
    cetane: float = 50.0
    lhv_mj_kg: float = 42.0
    api: float = 30.0

    def copy(self) -> "StreamProperties":
        return StreamProperties(
            sulfur_wt_pct=self.sulfur_wt_pct,
            density_kg_m3=self.density_kg_m3,
            ron=self.ron,
            cetane=self.cetane,
            lhv_mj_kg=self.lhv_mj_kg,
            api=self.api,
        )


def api_to_density(api: float) -> float:
    """API gravity to density (kg/m³) at 15 °C."""
    api = max(5.0, min(60.0, api))
    return 999.016 * 141.5 / (api + 131.5)


def density_to_api(density_kg_m3: float) -> float:
    sg = max(0.6, min(1.1, density_kg_m3 / 999.016))
    return 141.5 / sg - 131.5


def blend_properties(
    items: List[Tuple[float, StreamProperties]],
) -> StreamProperties:
    """Mass-linear blend for sulfur, cetane, RON; API via volume blend (ρ linear)."""
    total = sum(m for m, _ in items if m > 0)
    if total <= 0:
        return StreamProperties()
    wsum = 0.0
    sulfur = ron = cetane = lhv = 0.0
    vol = 0.0
    api_acc = 0.0
    for mass, props in items:
        if mass <= 0:
            continue
        w = mass / total
        wsum += w
        sulfur += w * props.sulfur_wt_pct
        ron += w * props.ron
        cetane += w * props.cetane
        lhv += w * props.lhv_mj_kg
        v = mass / max(props.density_kg_m3, 1.0)
        vol += v
        api_acc += w * props.api
    density = total / vol if vol > 0 else items[0][1].density_kg_m3
    return StreamProperties(
        sulfur_wt_pct=sulfur,
        density_kg_m3=density,
        ron=ron,
        cetane=cetane,
        lhv_mj_kg=lhv,
        api=density_to_api(density) if vol > 0 else api_acc,
    )


@dataclass
class PoolAccumulator:
    mass_mt_h: float = 0.0
    props: StreamProperties = field(default_factory=StreamProperties)

    def add(self, mass_mt_h: float, props: StreamProperties) -> None:
        if mass_mt_h <= 0:
            return
        if self.mass_mt_h <= 0:
            self.mass_mt_h = mass_mt_h
            self.props = props.copy()
            return
        self.props = blend_properties([(self.mass_mt_h, self.props), (mass_mt_h, props)])
        self.mass_mt_h += mass_mt_h


def default_props_for_cut(cut: str, sulfur_wt_pct: float = 1.0) -> StreamProperties:
    """Typical cut properties scaled from crude sulfur."""
    table = {
        "light_gas": StreamProperties(sulfur_wt_pct=0.0, density_kg_m3=1.2, ron=0, cetane=0, lhv_mj_kg=48.0, api=120),
        "lpg": StreamProperties(sulfur_wt_pct=0.01, density_kg_m3=520, ron=102, cetane=0, lhv_mj_kg=46.0, api=110),
        "naphtha": StreamProperties(sulfur_wt_pct=sulfur_wt_pct * 0.3, density_kg_m3=720, ron=68, cetane=0, lhv_mj_kg=44.0, api=55),
        "kerosene": StreamProperties(sulfur_wt_pct=sulfur_wt_pct * 0.5, density_kg_m3=780, ron=40, cetane=25, lhv_mj_kg=43.0, api=40),
        "diesel": StreamProperties(sulfur_wt_pct=sulfur_wt_pct * 0.7, density_kg_m3=840, ron=25, cetane=48, lhv_mj_kg=42.5, api=30),
        "gas_oil": StreamProperties(sulfur_wt_pct=sulfur_wt_pct * 0.9, density_kg_m3=900, ron=10, cetane=35, lhv_mj_kg=41.0, api=20),
        "vac_residue": StreamProperties(sulfur_wt_pct=sulfur_wt_pct * 1.2, density_kg_m3=980, ron=0, cetane=20, lhv_mj_kg=39.0, api=8),
        "gasoline": StreamProperties(sulfur_wt_pct=0.01, density_kg_m3=740, ron=92, cetane=0, lhv_mj_kg=44.0, api=60),
        "reformate": StreamProperties(sulfur_wt_pct=0.001, density_kg_m3=750, ron=100, cetane=0, lhv_mj_kg=43.0, api=58),
        "fcc_gasoline": StreamProperties(sulfur_wt_pct=0.02, density_kg_m3=735, ron=88, cetane=0, lhv_mj_kg=44.0, api=62),
    }
    return table.get(cut, StreamProperties(sulfur_wt_pct=sulfur_wt_pct)).copy()
