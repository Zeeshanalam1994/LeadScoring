"""Configuration and API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

UnitId = Literal["CDU", "VDU", "FCC", "HYDROCRACKER", "COKER", "CCR"]
PoolId = Literal["lpg", "kerosene", "diesel", "gasoline"]


class UnitNode(BaseModel):
    id: UnitId
    enabled: bool = True
    capacity_mt_h: float = Field(500.0, ge=0.0)
    params: Dict[str, float] = Field(default_factory=dict)


class StreamRoute(BaseModel):
    """Route a unit output port to another unit input or product pool."""

    from_unit: UnitId
    from_port: str
    to_unit: Optional[UnitId] = None
    to_pool: Optional[PoolId] = None
    split_fraction: float = Field(1.0, ge=0.0, le=1.0)


class RefineryConfig(BaseModel):
    crude_rate_mt_h: float = Field(1000.0, ge=1.0)
    crude_api: float = Field(31.0, ge=10.0, le=50.0)
    crude_sulfur_wt_pct: float = Field(2.5, ge=0.0, le=6.0)
    units: List[UnitNode] = Field(default_factory=list)
    routes: List[StreamRoute] = Field(default_factory=list)

    @staticmethod
    def default_config() -> "RefineryConfig":
        return RefineryConfig(
            crude_rate_mt_h=1000.0,
            units=[
                UnitNode(id="CDU", enabled=True, capacity_mt_h=1200, params={"recovery_eff": 0.995}),
                UnitNode(id="VDU", enabled=True, capacity_mt_h=400, params={"vgo_yield_wt": 0.55}),
                UnitNode(id="FCC", enabled=True, capacity_mt_h=250, params={"conversion_wt": 0.75}),
                UnitNode(id="HYDROCRACKER", enabled=True, capacity_mt_h=200, params={"conversion_wt": 0.85}),
                UnitNode(id="COKER", enabled=True, capacity_mt_h=150, params={"coke_yield_wt": 0.28}),
                UnitNode(id="CCR", enabled=True, capacity_mt_h=180, params={"reformate_yield_wt": 0.82}),
            ],
            routes=[],  # solver uses built-in default routing when empty
        )


class StreamResult(BaseModel):
    name: str
    flows: Dict[str, float]
    total_mt_h: float


class UnitResult(BaseModel):
    unit: UnitId
    feed_mt_h: float
    utilisation: float
    outputs: Dict[str, StreamResult]
    warnings: List[str] = Field(default_factory=list)


class PoolResult(BaseModel):
    pool: PoolId
    total_mt_h: float
    composition: Dict[str, float]


class SimulationResult(BaseModel):
    mass_balance_error_pct: float
    unit_results: List[UnitResult]
    pools: List[PoolResult]
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
