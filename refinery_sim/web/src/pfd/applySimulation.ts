import type { Edge, Node } from "@xyflow/react";
import type { SimulationResult, UnitId } from "../types";
import type { EquipmentNodeData, StreamEdgeData } from "./types";

const UNIT_IDS: UnitId[] = ["CDU", "VDU", "FCC", "HYDROCRACKER", "COKER", "CCR"];

export function applySimulationToPfd(
  nodes: Node[],
  edges: Edge[],
  result: SimulationResult,
): { nodes: Node[]; edges: Edge[] } {
  const unitMap = new Map(result.unit_results.map((u) => [u.unit, u]));
  const crude = Number(result.diagnostics.crude_mt_h ?? 0);

  const nextNodes = nodes.map((n) => {
    const d = { ...(n.data as EquipmentNodeData) };
    d.status = "ok";

    if (UNIT_IDS.includes(n.id as UnitId)) {
      const ur = unitMap.get(n.id as UnitId);
      if (ur) {
        d.subtitle = `${ur.feed_mt_h.toFixed(0)} MT/h · ${(ur.utilisation * 100).toFixed(0)}% cap`;
      }
      return { ...n, data: d };
    }

    const uid = d.unitId as UnitId | undefined;
    if (uid && UNIT_IDS.includes(uid)) {
      const ur = unitMap.get(uid);
      if (ur) {
        d.subtitle = `${ur.feed_mt_h.toFixed(0)} MT/h · ${(ur.utilisation * 100).toFixed(0)}% cap`;
      }
      return { ...n, data: d };
    }

    const hr = result.heaters.find((h) => `h_${h.unit_id}` === n.id);
    if (hr) {
      d.subtitle = `${hr.duty_mw.toFixed(1)} MW fired`;
      return { ...n, data: d };
    }

    if (n.id === "feeder" && result.feeders[0]) {
      const f = result.feeders[0];
      d.subtitle = `${f.total_rate_mt_h.toFixed(0)} MT/h · ${f.blended_api.toFixed(1)}° API`;
      return { ...n, data: d };
    }

    if (n.id === "fcc_riser") {
      const b = result.reactor_blocks.find((x) => x.block_type === "FCC_RISER_REACTOR");
      if (b) {
        d.subtitle = `Conv ${((b.metrics.conversion_wt ?? 0) * 100).toFixed(0)}% · ${(b.metrics.riser_duty_mw ?? 0).toFixed(1)} MW`;
      }
      return { ...n, data: d };
    }

    if (n.id === "fcc_regen") {
      const b = result.reactor_blocks.find((x) => x.block_type === "FCC_REGENERATOR");
      if (b) {
        d.subtitle = `${(b.metrics.regen_duty_mw ?? 0).toFixed(1)} MW · Flue ${(b.metrics.flue_gas_mt_h ?? 0).toFixed(0)} t/h`;
      }
      return { ...n, data: d };
    }

    if (n.id === "blend_gas") {
      const b = result.blenders.find((x) => x.blender_id === "bgas");
      if (b) d.subtitle = `${b.rate_mt_h.toFixed(0)} MT/h ${b.specs_met ? "✓ Spec" : "✗ Off spec"}`;
      return { ...n, data: d };
    }

    if (n.id === "blend_diesel") {
      const b = result.blenders.find((x) => x.blender_id === "bdiesel");
      if (b) d.subtitle = `${b.rate_mt_h.toFixed(0)} MT/h ${b.specs_met ? "✓ Spec" : "✗ Off spec"}`;
      return { ...n, data: d };
    }

    if (n.id.startsWith("pool_")) {
      const pool = n.id.replace("pool_", "");
      const p = result.pools.find((x) => x.pool === pool);
      if (p) d.subtitle = `${p.total_mt_h.toFixed(0)} MT/h inventory`;
      return { ...n, data: d };
    }

    return { ...n, data: d };
  });

  const flowByEdge: Record<string, number> = {
    "e-feed-cdu": crude,
    "e-cdu-vdu": unitMap.get("VDU")?.feed_mt_h ?? 0,
    "e-cdu-ccr": unitMap.get("CCR")?.feed_mt_h ?? 0,
    "e-vdu-riser": unitMap.get("FCC")?.feed_mt_h ?? 0,
    "e-vdu-hc": unitMap.get("HYDROCRACKER")?.feed_mt_h ?? 0,
    "e-vdu-coker": unitMap.get("COKER")?.feed_mt_h ?? 0,
    "e-fcc-gas": result.pools.find((p) => p.pool === "gasoline")?.total_mt_h ?? 0,
    "e-hc-diesel": unitMap.get("HYDROCRACKER")?.feed_mt_h ?? 0,
    "e-cdu-kero": result.pools.find((p) => p.pool === "kerosene")?.total_mt_h ?? 0,
    "e-cdu-diesel": result.pools.find((p) => p.pool === "diesel")?.total_mt_h ?? 0,
  };

  const nextEdges = edges.map((e) => {
    const flow = flowByEdge[e.id];
    if (flow === undefined) return e;
    const data = { ...(e.data as StreamEdgeData), flowMtH: flow };
    return { ...e, data };
  });

  return { nodes: nextNodes, edges: nextEdges };
}
