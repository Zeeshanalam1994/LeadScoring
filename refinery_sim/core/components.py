"""Pseudo-component stream model for refinery material balances."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

# Lumped boiling-range pseudo-components (mass basis, metric tons/hr in plant solve).
COMPONENTS: List[str] = [
    "light_gas",  # C1–C2, fuel gas
    "lpg",  # C3–C4
    "naphtha",  # ~IBP–180 °C
    "kerosene",  # ~180–250 °C
    "diesel",  # ~250–350 °C
    "gas_oil",  # ~350–565 °C (atm / VGO)
    "vac_residue",  # >565 °C vacuum bottoms
    "coke",  # solid carbonaceous
    "hydrogen",  # net H2 (negative = consumption)
]

PRODUCT_POOLS = ("lpg", "kerosene", "diesel", "gasoline")


@dataclass
class Stream:
    """Mass flow by pseudo-component (MT/h)."""

    flows: Dict[str, float] = field(default_factory=lambda: {c: 0.0 for c in COMPONENTS})
    name: str = "stream"

    def copy(self) -> "Stream":
        return Stream(name=self.name, flows=dict(self.flows))

    def total(self) -> float:
        # Hydrogen is tracked separately; exclude from hydrocarbon mass total.
        return sum(v for k, v in self.flows.items() if k != "hydrogen")

    def scale(self, factor: float) -> "Stream":
        out = self.copy()
        for k in out.flows:
            out.flows[k] *= factor
        return out

    def add(self, other: "Stream") -> "Stream":
        out = self.copy()
        for k in COMPONENTS:
            out.flows[k] += other.flows.get(k, 0.0)
        return out

    def subtract(self, other: "Stream") -> "Stream":
        out = self.copy()
        for k in COMPONENTS:
            out.flows[k] -= other.flows.get(k, 0.0)
        return out

    def blend(self, other: "Stream", fraction_self: float) -> "Stream":
        """Linear blend by mass fraction of this stream in the mixture."""
        f = max(0.0, min(1.0, fraction_self))
        out = Stream(name=f"{self.name}+{other.name}")
        for k in COMPONENTS:
            out.flows[k] = self.flows[k] * f + other.flows.get(k, 0.0) * (1.0 - f)
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, float], name: str = "stream") -> "Stream":
        s = cls(name=name)
        for k, v in data.items():
            if k in s.flows:
                s.flows[k] = float(v)
        return s

    def to_dict(self) -> Dict[str, float]:
        return dict(self.flows)

    def assert_nonnegative(self, tol: float = -1e-6) -> None:
        for k, v in self.flows.items():
            if v < tol:
                raise ValueError(f"Negative {k} ({v:.4f}) in stream {self.name}")


def empty_stream(name: str = "empty") -> Stream:
    return Stream(name=name)


def sum_streams(streams: Iterable[Stream], name: str = "sum") -> Stream:
    out = empty_stream(name)
    for s in streams:
        out = out.add(s)
    return out
