"""CCR multi-reactor train + stabilizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..components import Stream
from ..units import CCRParams, ccr_reformer


@dataclass
class CCRRigorousResult:
    products: Dict[str, Stream]
    wabt_c: float
    h2_yield_wt: float
    diagnostics: Dict[str, Any]


def ccr_rigorous_train(
    feed: Stream,
    reactor_params: Dict[str, float],
    stab_params: Dict[str, float],
) -> CCRRigorousResult:
    wabt = float(reactor_params.get("wabt_c", 510))
    n_rx = int(reactor_params.get("reactor_count", 4))
    pressure = float(reactor_params.get("pressure_mpa", 2.5))

    # WABT drives reformate yield and H2
    ref_y = 0.78 + 0.0004 * (wabt - 480) - 0.01 * (pressure - 2.5)
    ref_y = max(0.72, min(0.88, ref_y))
    h2_y = 0.025 + 0.00015 * (wabt - 480)

    ccr_p = CCRParams(reactor_pressure_mpa=pressure, reformate_yield_wt=ref_y, h2_yield_wt=h2_y)
    products = ccr_reformer(feed, ccr_p)

    overhead = float(stab_params.get("overhead_frac", 0.05))
    ref = products["reformate"]
    stab_gas = products["offgas"]
    move = ref.total() * overhead
    ref.flows["light_gas"] = ref.flows.get("light_gas", 0) - move * 0.3
    ref.flows["naphtha"] = max(0.0, ref.flows.get("naphtha", 0) - move * 0.7)
    stab_gas.flows["light_gas"] += move * 0.6
    stab_gas.flows["lpg"] += move * 0.4

    return CCRRigorousResult(
        products=products,
        wabt_c=wabt,
        h2_yield_wt=h2_y,
        diagnostics={"reactor_count": n_rx, "stabilizer_overhead_frac": overhead},
    )
