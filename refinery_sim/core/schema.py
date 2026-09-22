"""Configuration and API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

UnitId = Literal["CDU", "VDU", "FCC", "HYDROCRACKER", "COKER", "CCR"]
PoolId = Literal["lpg", "kerosene", "diesel", "gasoline"]


class AssayRecord(BaseModel):
    id: str
    name: str
    api: float = Field(31.0, ge=10.0, le=50.0)
    sulfur_wt_pct: float = Field(2.5, ge=0.0, le=6.0)
    yields: Dict[str, float] = Field(default_factory=dict)


class FeederComponent(BaseModel):
    assay_id: str
    rate_mt_h: float = Field(0.0, ge=0.0)


class CrudeFeeder(BaseModel):
    id: str = "main_feeder"
    name: str = "Crude blend to CDU"
    enabled: bool = True
    components: List[FeederComponent] = Field(default_factory=list)


class BlenderSourceModel(BaseModel):
    pool: PoolId
    tag: str = "default"
    fraction_of_pool: float = Field(1.0, ge=0.0, le=1.0)


class BlenderSpecModel(BaseModel):
    min_ron: Optional[float] = None
    max_ron: Optional[float] = None
    min_cetane: Optional[float] = None
    max_sulfur_wt_pct: Optional[float] = None
    min_density_kg_m3: Optional[float] = None
    max_density_kg_m3: Optional[float] = None


class ProductBlender(BaseModel):
    id: str
    name: str
    product: PoolId
    enabled: bool = True
    sources: List[BlenderSourceModel] = Field(default_factory=list)
    specs: BlenderSpecModel = Field(default_factory=BlenderSpecModel)


class HeaterConfig(BaseModel):
    id: str
    unit_id: UnitId
    name: str
    enabled: bool = True
    inlet_c: float = 120.0
    outlet_c: float = 350.0
    cp_kj_kg_k: float = 2.4
    thermal_efficiency: float = Field(0.92, ge=0.5, le=0.99)
    fuel_lhv_mj_kg: float = 45.0
    steam_generation_frac: float = Field(0.0, ge=0.0, le=0.5)


class UnitNode(BaseModel):
    id: UnitId
    enabled: bool = True
    capacity_mt_h: float = Field(500.0, ge=0.0)
    params: Dict[str, float] = Field(default_factory=dict)


class StreamRoute(BaseModel):
    from_unit: UnitId
    from_port: str
    to_unit: Optional[UnitId] = None
    to_pool: Optional[PoolId] = None
    split_fraction: float = Field(1.0, ge=0.0, le=1.0)


class RefineryConfig(BaseModel):
    crude_rate_mt_h: float = Field(1000.0, ge=0.0)
    crude_api: float = Field(31.0, ge=10.0, le=50.0)
    crude_sulfur_wt_pct: float = Field(2.5, ge=0.0, le=6.0)
    assays: List[AssayRecord] = Field(default_factory=list)
    feeders: List[CrudeFeeder] = Field(default_factory=list)
    blenders: List[ProductBlender] = Field(default_factory=list)
    heaters: List[HeaterConfig] = Field(default_factory=list)
    flare_fraction: float = Field(0.02, ge=0.0, le=0.2)
    units: List[UnitNode] = Field(default_factory=list)
    routes: List[StreamRoute] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_legacy_crude(self) -> "RefineryConfig":
        if not self.assays:
            from refinery_sim.core.feeders import default_assay_library

            lib = default_assay_library()
            self.assays = [
                AssayRecord(
                    id=k,
                    name=v.name,
                    api=v.api,
                    sulfur_wt_pct=v.sulfur_wt_pct,
                    yields=dict(v.yields),
                )
                for k, v in lib.items()
            ]
        if not self.feeders:
            self.feeders = [
                CrudeFeeder(
                    id="main_feeder",
                    name="Primary crude blend",
                    components=[
                        FeederComponent(assay_id="arab_medium", rate_mt_h=self.crude_rate_mt_h * 0.7),
                        FeederComponent(assay_id="light_sweet", rate_mt_h=self.crude_rate_mt_h * 0.3),
                    ],
                )
            ]
        if not self.heaters:
            from refinery_sim.core.heaters import default_heater_map

            self.heaters = [
                HeaterConfig(
                    id=h.id,
                    unit_id=h.unit_id,
                    name=h.name,
                    inlet_c=h.inlet_c,
                    outlet_c=h.outlet_c,
                    cp_kj_kg_k=h.cp_kj_kg_k,
                    thermal_efficiency=h.thermal_efficiency,
                    fuel_lhv_mj_kg=h.fuel_lhv_mj_kg,
                    steam_generation_frac=h.steam_generation_frac,
                )
                for h in default_heater_map().values()
            ]
        if not self.blenders:
            self.blenders = [
                ProductBlender(
                    id="bgas",
                    name="Motor gasoline blender",
                    product="gasoline",
                    sources=[
                        BlenderSourceModel(pool="gasoline", tag="fcc", fraction_of_pool=0.55),
                        BlenderSourceModel(pool="gasoline", tag="ccr", fraction_of_pool=1.0),
                        BlenderSourceModel(pool="gasoline", tag="straight_run", fraction_of_pool=0.35),
                    ],
                    specs=BlenderSpecModel(min_ron=91.0, max_sulfur_wt_pct=0.01),
                ),
                ProductBlender(
                    id="bdiesel",
                    name="ULSD blender",
                    product="diesel",
                    sources=[
                        BlenderSourceModel(pool="diesel", tag="straight_run", fraction_of_pool=0.5),
                        BlenderSourceModel(pool="diesel", tag="hc", fraction_of_pool=1.0),
                        BlenderSourceModel(pool="diesel", tag="lco", fraction_of_pool=0.4),
                    ],
                    specs=BlenderSpecModel(min_cetane=51.0, max_sulfur_wt_pct=0.001),
                ),
            ]
        return self

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
            routes=[],
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
    properties: Dict[str, float] = Field(default_factory=dict)


class HeaterResultModel(BaseModel):
    id: str
    unit_id: UnitId
    name: str
    feed_mt_h: float
    duty_mw: float
    fuel_mt_h: float
    steam_generated_mt_h: float
    co2_mt_h: float


class BlenderResultModel(BaseModel):
    blender_id: str
    name: str
    product: PoolId
    rate_mt_h: float
    properties: Dict[str, float]
    specs_met: bool
    violations: List[str] = Field(default_factory=list)


class FeederComponentResult(BaseModel):
    assay_id: str
    rate_mt_h: float


class FeederResultModel(BaseModel):
    feeder_id: str
    name: str
    total_rate_mt_h: float
    blended_api: float
    blended_sulfur_wt_pct: float
    components: List[FeederComponentResult]


class EnergyResultModel(BaseModel):
    total_duty_mw: float
    total_fuel_mt_h: float
    steam_generated_mt_h: float
    steam_consumed_mt_h: float
    net_steam_mt_h: float
    specific_energy_gj_per_mt_crude: float
    electricity_equivalent_mw: float


class EmissionsResultModel(BaseModel):
    co2_fuel_mt_h: float
    co2_flare_mt_h: float
    co2_total_mt_h: float
    so2_kg_h: float
    nox_kg_h: float
    co2_specific_kg_per_mt_crude: float


class SimulationResult(BaseModel):
    mass_balance_error_pct: float
    unit_results: List[UnitResult]
    pools: List[PoolResult]
    feeders: List[FeederResultModel] = Field(default_factory=list)
    blenders: List[BlenderResultModel] = Field(default_factory=list)
    heaters: List[HeaterResultModel] = Field(default_factory=list)
    energy: Optional[EnergyResultModel] = None
    emissions: Optional[EmissionsResultModel] = None
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
