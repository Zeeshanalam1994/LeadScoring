"""Refinery-wide material balance solver."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .components import PRODUCT_POOLS, Stream, empty_stream, sum_streams
from .crude import BENCHMARK_CRUDE, CDUCutPoints, CrudeAssay, crude_feed_stream, cdu_split
from .schema import PoolResult, RefineryConfig, SimulationResult, StreamResult, UnitResult
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

    def solve(self) -> SimulationResult:
        assay = self._assay_from_config()
        crude = crude_feed_stream(self.config.crude_rate_mt_h, assay)
        unit_results: List[UnitResult] = []
        warnings: List[str] = []

        # --- CDU ---
        cdu_node = self._unit_map.get("CDU")
        if not cdu_node or not cdu_node.enabled:
            raise ValueError("CDU must be enabled for refinery simulation")

        cdu_feed = self._cap_stream(crude, cdu_node.capacity_mt_h)
        cuts = CDUCutPoints()
        rec_eff = float(cdu_node.params.get("recovery_eff", 0.995))
        cdu_out = cdu_split(cdu_feed, cuts, recovery_eff=rec_eff)
        unit_results.append(
            self._pack_unit("CDU", cdu_feed, cdu_out, cdu_node.capacity_mt_h)
        )

        # Default internal routing (configurable later via routes)
        atm_res = cdu_out["atm_residue"]
        naphtha = cdu_out["naphtha"]
        kero_cut = cdu_out["kerosene"]
        diesel_cut = cdu_out["diesel"]
        offgas = cdu_out["offgas_lpg"]

        pool_accum: Dict[str, Stream] = {p: empty_stream(f"pool_{p}") for p in PRODUCT_POOLS}

        # Direct CDU cuts to pools
        pool_accum["lpg"] = pool_accum["lpg"].add(offgas)
        pool_accum["kerosene"] = pool_accum["kerosene"].add(kero_cut)
        pool_accum["diesel"] = pool_accum["diesel"].add(diesel_cut)

        vgo_for_downstream = empty_stream("vgo_pool")

        # --- VDU ---
        vdu_node = self._unit_map.get("VDU")
        if vdu_node and vdu_node.enabled:
            vdu_feed = self._cap_stream(atm_res, vdu_node.capacity_mt_h)
            vdu_p = VDUParams(
                vgo_yield_wt=float(vdu_node.params.get("vgo_yield_wt", 0.55)),
                vr_yield_wt=float(vdu_node.params.get("vr_yield_wt", 0.43)),
            )
            vdu_out = vdu_split(vdu_feed, vdu_p)
            unit_results.append(self._pack_unit("VDU", vdu_feed, vdu_out, vdu_node.capacity_mt_h))
            vgo_for_downstream = vgo_for_downstream.add(vdu_out["vgo"])
            pool_accum["lpg"] = pool_accum["lpg"].add(vdu_out["offgas"])
            vr_feed = vdu_out["vac_residue"]
        else:
            vr_feed = atm_res
            vgo_for_downstream = vgo_for_downstream.add(
                Stream.from_dict({"gas_oil": atm_res.total() * 0.3}, "atm_vgo_proxy")
            )

        # Split VGO between FCC and Hydrocracker (50/50 default, tunable)
        fcc_node = self._unit_map.get("FCC")
        fcc_share = float(fcc_node.params.get("feed_share", 0.55)) if fcc_node else 0.55
        hc_share = 1.0 - fcc_share
        fcc_feed = vgo_for_downstream.scale(fcc_share)
        hc_feed = vgo_for_downstream.scale(hc_share)

        # --- FCC ---
        if fcc_node and fcc_node.enabled:
            fcc_feed_c = self._cap_stream(fcc_feed, fcc_node.capacity_mt_h)
            fcc_p = FCCParams(
                conversion_wt=float(fcc_node.params.get("conversion_wt", 0.75)),
                coke_make_wt=float(fcc_node.params.get("coke_make_wt", 0.06)),
            )
            fcc_out = fcc_reactor(fcc_feed_c, fcc_p)
            unit_results.append(self._pack_unit("FCC", fcc_feed_c, fcc_out, fcc_node.capacity_mt_h))
            pool_accum["lpg"] = pool_accum["lpg"].add(fcc_out["lpg"]).add(fcc_out["offgas"])
            pool_accum["gasoline"] = pool_accum["gasoline"].add(fcc_out["gasoline"])
            pool_accum["diesel"] = pool_accum["diesel"].add(fcc_out["lco"])

        # --- Hydrocracker ---
        hc_node = self._unit_map.get("HYDROCRACKER")
        h2_supply = empty_stream("h2_supply")
        if hc_node and hc_node.enabled:
            hc_feed_c = self._cap_stream(hc_feed, hc_node.capacity_mt_h)
            hc_p = HydrocrackerParams(
                conversion_wt=float(hc_node.params.get("conversion_wt", 0.85)),
                h2_consumption_wt=float(hc_node.params.get("h2_consumption_wt", 0.025)),
            )
            hc_out = hydrocracker(hc_feed_c, hc_p)
            unit_results.append(self._pack_unit("HYDROCRACKER", hc_feed_c, hc_out, hc_node.capacity_mt_h))
            pool_accum["kerosene"] = pool_accum["kerosene"].add(hc_out["kerosene"])
            pool_accum["diesel"] = pool_accum["diesel"].add(hc_out["diesel"])
            pool_accum["gasoline"] = pool_accum["gasoline"].add(hc_out["naphtha"])
            pool_accum["lpg"] = pool_accum["lpg"].add(hc_out["offgas"])
            h2_supply = h2_supply.add(Stream.from_dict({"hydrogen": hc_out["offgas"].flows.get("hydrogen", 0.0)}))

        # --- Coker ---
        coker_node = self._unit_map.get("COKER")
        if coker_node and coker_node.enabled:
            coker_feed_c = self._cap_stream(vr_feed, coker_node.capacity_mt_h)
            coker_p = CokerParams(coke_yield_wt=float(coker_node.params.get("coke_yield_wt", 0.28)))
            coker_out = delayed_coker(coker_feed_c, coker_p)
            unit_results.append(self._pack_unit("COKER", coker_feed_c, coker_out, coker_node.capacity_mt_h))
            pool_accum["lpg"] = pool_accum["lpg"].add(coker_out["lpg"]).add(coker_out["offgas"])
            pool_accum["gasoline"] = pool_accum["gasoline"].add(coker_out["naphtha"])
            pool_accum["diesel"] = pool_accum["diesel"].add(coker_out["lco"])

        # --- CCR ---
        ccr_node = self._unit_map.get("CCR")
        if ccr_node and ccr_node.enabled:
            ccr_feed_c = self._cap_stream(naphtha, ccr_node.capacity_mt_h)
            ccr_p = CCRParams(reformate_yield_wt=float(ccr_node.params.get("reformate_yield_wt", 0.82)))
            ccr_out = ccr_reformer(ccr_feed_c, ccr_p)
            unit_results.append(self._pack_unit("CCR", ccr_feed_c, ccr_out, ccr_node.capacity_mt_h))
            pool_accum["gasoline"] = pool_accum["gasoline"].add(ccr_out["reformate"])
            pool_accum["lpg"] = pool_accum["lpg"].add(ccr_out["offgas"])
            h2_supply = h2_supply.add(ccr_out["h2"])

        # Gasoline pool also receives uncatalyzed naphtha bypass (remainder after CCR)
        naph_bypass = naphtha.scale(max(0.0, 1.0 - min(1.0, (ccr_node.capacity_mt_h if ccr_node else 0) / max(naphtha.total(), 1e-6))))
        pool_accum["gasoline"] = pool_accum["gasoline"].add(naph_bypass)

        pools = self._pack_pools(pool_accum)
        total_in = crude.total()
        total_out = sum(p.total_mt_h for p in pools) + sum(
            ur.outputs.get("coke", StreamResult(name="coke", flows={}, total_mt_h=0)).total_mt_h
            for ur in unit_results
            if "coke" in ur.outputs
        )
        mb_error = 100.0 * abs(total_in - total_out) / max(total_in, 1e-6)

        return SimulationResult(
            mass_balance_error_pct=mb_error,
            unit_results=unit_results,
            pools=pools,
            diagnostics={
                "crude_mt_h": total_in,
                "total_products_mt_h": total_out,
                "h2_net_mt_h": h2_supply.flows.get("hydrogen", 0.0),
                "warnings": warnings,
            },
        )

    def _assay_from_config(self) -> CrudeAssay:
        base = BENCHMARK_CRUDE
        return CrudeAssay(
            name=f"User_{self.config.crude_api:.0f}API",
            api=self.config.crude_api,
            sulfur_wt_pct=self.config.crude_sulfur_wt_pct,
            yields=dict(base.yields),
        )

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
    def _pack_unit(
        unit_id: str, feed: Stream, outputs: Dict[str, Stream], capacity: float
    ) -> UnitResult:
        feed_mt = feed.total()
        util = feed_mt / capacity if capacity > 0 else 0.0
        warns = []
        if util > 1.001:
            warns.append(f"Feed exceeds capacity ({util:.1%})")
        out_packed = {
            k: StreamResult(name=v.name, flows=v.to_dict(), total_mt_h=v.total())
            for k, v in outputs.items()
        }
        return UnitResult(unit=unit_id, feed_mt_h=feed_mt, utilisation=util, outputs=out_packed, warnings=warns)

    @staticmethod
    def _pack_pools(pool_accum: Dict[str, Stream]) -> List[PoolResult]:
        results = []
        for pid in PRODUCT_POOLS:
            s = pool_accum[pid]
            comp = {k: v for k, v in s.flows.items() if abs(v) > 1e-6}
            results.append(PoolResult(pool=pid, total_mt_h=s.total(), composition=comp))
        return results
