"""Refinery-wide material balance, energy, and emissions solver."""

from __future__ import annotations

from typing import Dict, List, Tuple

from .blending import BlenderDefinition, BlenderSpecs, BlenderSource, run_blender
from .components import PRODUCT_POOLS, Stream, empty_stream
from .crude import CDUCutPoints, cdu_split
from .energy_emissions import aggregate_emissions, aggregate_energy
from .feeders import assay_from_record, build_crude_charge
from .heaters import HeaterModel, HeaterResult, simulate_heater
from .properties import PoolAccumulator, default_props_for_cut, blend_properties
from .schema import (
    BlenderResultModel,
    EmissionsResultModel,
    EnergyResultModel,
    FeederComponentResult,
    FeederResultModel,
    HeaterResultModel,
    PoolResult,
    RefineryConfig,
    SimulationResult,
    StreamResult,
    UnitId,
    UnitResult,
)
from .units import (
    CCRParams,
    CokerParams,
    FCCParams,
    HydrocrackerParams,
    VDUParams,
    ccr_reformer,
    delayed_coker,
    fcc_reactor,
    hydrocracker,
    vdu_split,
)


class RefinerySolver:
    def __init__(self, config: RefineryConfig):
        self.config = config
        self._unit_map = {u.id: u for u in config.units}
        self._heater_map = {h.unit_id: h for h in config.heaters}

    def solve(self) -> SimulationResult:
        crude, feeder_results, crude_sulfur = self._build_crude_feed()
        unit_results: List[UnitResult] = []
        heater_results: List[HeaterResultModel] = []
        heater_sims: List[HeaterResult] = []
        unit_feed_rates: Dict[UnitId, float] = {}
        warnings: List[str] = []

        pool_accum: Dict[str, Stream] = {p: empty_stream(f"pool_{p}") for p in PRODUCT_POOLS}
        pool_tags: Dict[str, Dict[str, PoolAccumulator]] = {p: {} for p in PRODUCT_POOLS}

        # --- CDU ---
        cdu_node = self._unit_map.get("CDU")
        if not cdu_node or not cdu_node.enabled:
            raise ValueError("CDU must be enabled for refinery simulation")

        cdu_feed = self._cap_stream(crude, cdu_node.capacity_mt_h)
        unit_feed_rates["CDU"] = cdu_feed.total()
        self._run_heater("CDU", cdu_feed.total(), heater_results, heater_sims)

        cuts = CDUCutPoints()
        rec_eff = float(cdu_node.params.get("recovery_eff", 0.995))
        cdu_out = cdu_split(cdu_feed, cuts, recovery_eff=rec_eff)
        unit_results.append(self._pack_unit("CDU", cdu_feed, cdu_out, cdu_node.capacity_mt_h))

        atm_res = cdu_out["atm_residue"]
        naphtha = cdu_out["naphtha"]
        kero_cut = cdu_out["kerosene"]
        diesel_cut = cdu_out["diesel"]
        offgas = cdu_out["offgas_lpg"]

        self._to_pool(pool_accum, pool_tags, "lpg", "default", offgas, default_props_for_cut("lpg"))
        self._to_pool(
            pool_accum,
            pool_tags,
            "kerosene",
            "straight_run",
            kero_cut,
            default_props_for_cut("kerosene", crude_sulfur),
        )
        self._to_pool(
            pool_accum,
            pool_tags,
            "diesel",
            "straight_run",
            diesel_cut,
            default_props_for_cut("diesel", crude_sulfur),
        )

        vgo_for_downstream = empty_stream("vgo_pool")

        # --- VDU ---
        vdu_node = self._unit_map.get("VDU")
        if vdu_node and vdu_node.enabled:
            vdu_feed = self._cap_stream(atm_res, vdu_node.capacity_mt_h)
            unit_feed_rates["VDU"] = vdu_feed.total()
            self._run_heater("VDU", vdu_feed.total(), heater_results, heater_sims)
            vdu_p = VDUParams(
                vgo_yield_wt=float(vdu_node.params.get("vgo_yield_wt", 0.55)),
                vr_yield_wt=float(vdu_node.params.get("vr_yield_wt", 0.43)),
            )
            vdu_out = vdu_split(vdu_feed, vdu_p)
            unit_results.append(self._pack_unit("VDU", vdu_feed, vdu_out, vdu_node.capacity_mt_h))
            vgo_for_downstream = vgo_for_downstream.add(vdu_out["vgo"])
            self._to_pool(pool_accum, pool_tags, "lpg", "default", vdu_out["offgas"], default_props_for_cut("light_gas"))
            vr_feed = vdu_out["vac_residue"]
        else:
            vr_feed = atm_res
            vgo_for_downstream = vgo_for_downstream.add(
                Stream.from_dict({"gas_oil": atm_res.total() * 0.3}, "atm_vgo_proxy")
            )

        fcc_node = self._unit_map.get("FCC")
        fcc_share = float(fcc_node.params.get("feed_share", 0.55)) if fcc_node else 0.55
        fcc_feed = vgo_for_downstream.scale(fcc_share)
        hc_feed = vgo_for_downstream.scale(1.0 - fcc_share)

        # --- FCC ---
        if fcc_node and fcc_node.enabled:
            fcc_feed_c = self._cap_stream(fcc_feed, fcc_node.capacity_mt_h)
            unit_feed_rates["FCC"] = fcc_feed_c.total()
            self._run_heater("FCC", fcc_feed_c.total(), heater_results, heater_sims)
            fcc_p = FCCParams(
                conversion_wt=float(fcc_node.params.get("conversion_wt", 0.75)),
                coke_make_wt=float(fcc_node.params.get("coke_make_wt", 0.06)),
            )
            fcc_out = fcc_reactor(fcc_feed_c, fcc_p)
            unit_results.append(self._pack_unit("FCC", fcc_feed_c, fcc_out, fcc_node.capacity_mt_h))
            self._to_pool(pool_accum, pool_tags, "lpg", "fcc", fcc_out["lpg"], default_props_for_cut("lpg"))
            self._to_pool(pool_accum, pool_tags, "lpg", "default", fcc_out["offgas"], default_props_for_cut("light_gas"))
            self._to_pool(
                pool_accum,
                pool_tags,
                "gasoline",
                "fcc",
                fcc_out["gasoline"],
                default_props_for_cut("fcc_gasoline"),
            )
            self._to_pool(
                pool_accum,
                pool_tags,
                "diesel",
                "lco",
                fcc_out["lco"],
                default_props_for_cut("diesel", crude_sulfur * 0.8),
            )

        # --- Hydrocracker ---
        hc_node = self._unit_map.get("HYDROCRACKER")
        h2_supply = empty_stream("h2_supply")
        if hc_node and hc_node.enabled:
            hc_feed_c = self._cap_stream(hc_feed, hc_node.capacity_mt_h)
            unit_feed_rates["HYDROCRACKER"] = hc_feed_c.total()
            self._run_heater("HYDROCRACKER", hc_feed_c.total(), heater_results, heater_sims)
            hc_p = HydrocrackerParams(
                conversion_wt=float(hc_node.params.get("conversion_wt", 0.85)),
                h2_consumption_wt=float(hc_node.params.get("h2_consumption_wt", 0.025)),
            )
            hc_out = hydrocracker(hc_feed_c, hc_p)
            unit_results.append(self._pack_unit("HYDROCRACKER", hc_feed_c, hc_out, hc_node.capacity_mt_h))
            self._to_pool(
                pool_accum,
                pool_tags,
                "kerosene",
                "hc",
                hc_out["kerosene"],
                default_props_for_cut("kerosene", crude_sulfur * 0.2),
            )
            self._to_pool(
                pool_accum,
                pool_tags,
                "diesel",
                "hc",
                hc_out["diesel"],
                default_props_for_cut("diesel", crude_sulfur * 0.1),
            )
            self._to_pool(
                pool_accum,
                pool_tags,
                "gasoline",
                "hc_naphtha",
                hc_out["naphtha"],
                default_props_for_cut("naphtha", crude_sulfur * 0.15),
            )
            self._to_pool(pool_accum, pool_tags, "lpg", "default", hc_out["offgas"], default_props_for_cut("light_gas"))
            h2_supply = h2_supply.add(Stream.from_dict({"hydrogen": hc_out["offgas"].flows.get("hydrogen", 0.0)}))

        # --- Coker ---
        coker_node = self._unit_map.get("COKER")
        if coker_node and coker_node.enabled:
            coker_feed_c = self._cap_stream(vr_feed, coker_node.capacity_mt_h)
            unit_feed_rates["COKER"] = coker_feed_c.total()
            self._run_heater("COKER", coker_feed_c.total(), heater_results, heater_sims)
            coker_p = CokerParams(coke_yield_wt=float(coker_node.params.get("coke_yield_wt", 0.28)))
            coker_out = delayed_coker(coker_feed_c, coker_p)
            unit_results.append(self._pack_unit("COKER", coker_feed_c, coker_out, coker_node.capacity_mt_h))
            self._to_pool(pool_accum, pool_tags, "lpg", "coker", coker_out["lpg"], default_props_for_cut("lpg"))
            self._to_pool(pool_accum, pool_tags, "lpg", "default", coker_out["offgas"], default_props_for_cut("light_gas"))
            self._to_pool(
                pool_accum,
                pool_tags,
                "gasoline",
                "coker_naphtha",
                coker_out["naphtha"],
                default_props_for_cut("naphtha", crude_sulfur),
            )
            self._to_pool(
                pool_accum,
                pool_tags,
                "diesel",
                "lco",
                coker_out["lco"],
                default_props_for_cut("diesel", crude_sulfur),
            )

        # --- CCR ---
        ccr_node = self._unit_map.get("CCR")
        if ccr_node and ccr_node.enabled:
            ccr_feed_c = self._cap_stream(naphtha, ccr_node.capacity_mt_h)
            unit_feed_rates["CCR"] = ccr_feed_c.total()
            self._run_heater("CCR", ccr_feed_c.total(), heater_results, heater_sims)
            ccr_p = CCRParams(reformate_yield_wt=float(ccr_node.params.get("reformate_yield_wt", 0.82)))
            ccr_out = ccr_reformer(ccr_feed_c, ccr_p)
            unit_results.append(self._pack_unit("CCR", ccr_feed_c, ccr_out, ccr_node.capacity_mt_h))
            self._to_pool(
                pool_accum,
                pool_tags,
                "gasoline",
                "ccr",
                ccr_out["reformate"],
                default_props_for_cut("reformate"),
            )
            self._to_pool(pool_accum, pool_tags, "lpg", "default", ccr_out["offgas"], default_props_for_cut("light_gas"))
            h2_supply = h2_supply.add(ccr_out["h2"])

        ccr_cap = ccr_node.capacity_mt_h if ccr_node else 0.0
        naph_total = naphtha.total()
        bypass_frac = max(0.0, 1.0 - min(1.0, ccr_cap / max(naph_total, 1e-6)))
        naph_bypass = naphtha.scale(bypass_frac)
        self._to_pool(
            pool_accum,
            pool_tags,
            "gasoline",
            "straight_run",
            naph_bypass,
            default_props_for_cut("naphtha", crude_sulfur),
        )

        pools = self._pack_pools(pool_accum, pool_tags)
        blender_results = self._run_blenders(pool_tags)

        total_in = crude.total()
        coke_mt = sum(
            ur.outputs.get("coke", StreamResult(name="coke", flows={}, total_mt_h=0)).total_mt_h
            for ur in unit_results
            if "coke" in ur.outputs
        )
        total_out = sum(p.total_mt_h for p in pools) + coke_mt
        mb_error = 100.0 * abs(total_in - total_out) / max(total_in, 1e-6)

        flare_gas = pool_accum["lpg"].flows.get("light_gas", 0.0) * self.config.flare_fraction
        energy = aggregate_energy(heater_sims, unit_feed_rates, total_in)
        emissions = aggregate_emissions(heater_sims, flare_gas, total_in)

        return SimulationResult(
            mass_balance_error_pct=mb_error,
            unit_results=unit_results,
            pools=pools,
            feeders=feeder_results,
            blenders=[
                BlenderResultModel(
                    blender_id=b.blender_id,
                    name=b.name,
                    product=b.product,
                    rate_mt_h=b.rate_mt_h,
                    properties=b.properties,
                    specs_met=b.specs_met,
                    violations=b.violations,
                )
                for b in blender_results
            ],
            heaters=heater_results,
            energy=EnergyResultModel(
                total_duty_mw=energy.total_duty_mw,
                total_fuel_mt_h=energy.total_fuel_mt_h,
                steam_generated_mt_h=energy.steam_generated_mt_h,
                steam_consumed_mt_h=energy.steam_consumed_mt_h,
                net_steam_mt_h=energy.net_steam_mt_h,
                specific_energy_gj_per_mt_crude=energy.specific_energy_gj_per_mt_crude,
                electricity_equivalent_mw=energy.electricity_equivalent_mw,
            ),
            emissions=EmissionsResultModel(
                co2_fuel_mt_h=emissions.co2_fuel_mt_h,
                co2_flare_mt_h=emissions.co2_flare_mt_h,
                co2_total_mt_h=emissions.co2_total_mt_h,
                so2_kg_h=emissions.so2_kg_h,
                nox_kg_h=emissions.nox_kg_h,
                co2_specific_kg_per_mt_crude=emissions.co2_specific_kg_per_mt_crude,
            ),
            diagnostics={
                "crude_mt_h": total_in,
                "total_products_mt_h": total_out,
                "h2_net_mt_h": h2_supply.flows.get("hydrogen", 0.0),
                "flare_gas_mt_h": flare_gas,
                "warnings": warnings,
            },
        )

    def _build_crude_feed(self) -> Tuple[Stream, List[FeederResultModel], float]:
        assays = {a.id: assay_from_record(a.model_dump()) for a in self.config.assays}
        streams: List[Stream] = []
        feeder_results: List[FeederResultModel] = []
        sulfur = self.config.crude_sulfur_wt_pct

        if self.config.feeders:
            for feeder in self.config.feeders:
                if not feeder.enabled:
                    continue
                comps = [(c.assay_id, c.rate_mt_h) for c in feeder.components if c.rate_mt_h > 0]
                if not comps:
                    continue
                stream, _assay, props, rate = build_crude_charge(assays, comps)
                streams.append(stream)
                feeder_results.append(
                    FeederResultModel(
                        feeder_id=feeder.id,
                        name=feeder.name,
                        total_rate_mt_h=rate,
                        blended_api=props.api,
                        blended_sulfur_wt_pct=props.sulfur_wt_pct,
                        components=[FeederComponentResult(assay_id=a, rate_mt_h=r) for a, r in comps],
                    )
                )
                sulfur = props.sulfur_wt_pct
        else:
            from .crude import BENCHMARK_CRUDE, crude_feed_stream

            assay = BENCHMARK_CRUDE
            streams.append(crude_feed_stream(self.config.crude_rate_mt_h, assay))
            sulfur = assay.sulfur_wt_pct

        if not streams:
            raise ValueError("No crude feeders enabled — define at least one assay component")

        crude = streams[0]
        for s in streams[1:]:
            crude = crude.add(s)
        crude.name = "total_crude_charge"
        return crude, feeder_results, sulfur

    def _run_heater(
        self,
        unit_id: UnitId,
        feed_mt_h: float,
        out: List[HeaterResultModel],
        sims: List[HeaterResult],
    ) -> None:
        hc = self._heater_map.get(unit_id)
        if hc is None or not hc.enabled:
            return
        model = HeaterModel(
            id=hc.id,
            unit_id=hc.unit_id,
            name=hc.name,
            inlet_c=hc.inlet_c,
            outlet_c=hc.outlet_c,
            cp_kj_kg_k=hc.cp_kj_kg_k,
            thermal_efficiency=hc.thermal_efficiency,
            fuel_lhv_mj_kg=hc.fuel_lhv_mj_kg,
            steam_generation_frac=hc.steam_generation_frac,
        )
        res = simulate_heater(model, feed_mt_h)
        sims.append(res)
        out.append(
            HeaterResultModel(
                id=res.id,
                unit_id=res.unit_id,
                name=res.name,
                feed_mt_h=res.feed_mt_h,
                duty_mw=res.duty_mw,
                fuel_mt_h=res.fuel_mt_h,
                steam_generated_mt_h=res.steam_generated_mt_h,
                co2_mt_h=res.co2_mt_h,
            )
        )

    def _run_blenders(self, pool_tags: Dict[str, Dict[str, PoolAccumulator]]):
        results = []
        for b in self.config.blenders:
            if not b.enabled:
                continue
            defn = BlenderDefinition(
                id=b.id,
                name=b.name,
                product=b.product,
                sources=[
                    BlenderSource(pool=s.pool, tag=s.tag, fraction_of_pool=s.fraction_of_pool) for s in b.sources
                ],
                specs=BlenderSpecs(
                    min_ron=b.specs.min_ron,
                    max_ron=b.specs.max_ron,
                    min_cetane=b.specs.min_cetane,
                    max_sulfur_wt_pct=b.specs.max_sulfur_wt_pct,
                    min_density_kg_m3=b.specs.min_density_kg_m3,
                    max_density_kg_m3=b.specs.max_density_kg_m3,
                ),
            )
            results.append(run_blender(defn, pool_tags))
        return results

    @staticmethod
    def _to_pool(
        pool_accum: Dict[str, Stream],
        pool_tags: Dict[str, Dict[str, PoolAccumulator]],
        pool: str,
        tag: str,
        stream: Stream,
        props,
    ) -> None:
        pool_accum[pool] = pool_accum[pool].add(stream)
        mass = stream.total()
        if mass <= 0:
            return
        if tag not in pool_tags[pool]:
            pool_tags[pool][tag] = PoolAccumulator()
        pool_tags[pool][tag].add(mass, props)

    @staticmethod
    def _cap_stream(s: Stream, cap: float) -> Stream:
        t = s.total()
        if t <= cap or cap <= 0:
            return s.copy()
        w = cap / t
        out = s.scale(w)
        out.name = s.name + "_capped"
        return out

    @staticmethod
    def _pack_unit(unit_id: str, feed: Stream, outputs: Dict[str, Stream], capacity: float) -> UnitResult:
        feed_mt = feed.total()
        util = feed_mt / capacity if capacity > 0 else 0.0
        warns = []
        if util > 1.001:
            warns.append(f"Feed exceeds capacity ({util:.1%})")
        out_packed = {
            k: StreamResult(name=v.name, flows=v.to_dict(), total_mt_h=v.total()) for k, v in outputs.items()
        }
        return UnitResult(unit=unit_id, feed_mt_h=feed_mt, utilisation=util, outputs=out_packed, warnings=warns)

    @staticmethod
    def _pack_pools(pool_accum: Dict[str, Stream], pool_tags: Dict[str, Dict[str, PoolAccumulator]]) -> List[PoolResult]:
        results = []
        for pid in PRODUCT_POOLS:
            s = pool_accum[pid]
            comp = {k: v for k, v in s.flows.items() if abs(v) > 1e-6}
            tag_items = []
            for tag, acc in pool_tags.get(pid, {}).items():
                if acc.mass_mt_h > 0:
                    tag_items.append((acc.mass_mt_h, acc.props))
            props = blend_properties(tag_items) if tag_items else None
            prop_dict = (
                {
                    "sulfur_wt_pct": props.sulfur_wt_pct,
                    "density_kg_m3": props.density_kg_m3,
                    "ron": props.ron,
                    "cetane": props.cetane,
                    "api": props.api,
                }
                if props
                else {}
            )
            results.append(PoolResult(pool=pid, total_mt_h=s.total(), composition=comp, properties=prop_dict))
        return results
