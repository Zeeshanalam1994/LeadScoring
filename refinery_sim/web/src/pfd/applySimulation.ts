import type { Edge, Node } from "@xyflow/react";
import type { SimulationResult, UnitId } from "../types";
import type { EquipmentNodeData, StreamEdgeData } from "./types";

const UNIT_IDS: UnitId[] = ["CDU", "VDU", "FCC", "HYDROCRACKER", "COKER", "CCR"];

/** Map PFD edge id → simulation unit output port name */
const EDGE_PORT: Record<string, { unit: UnitId; port: string }> = {
  "e-cdu-offgas": { unit: "CDU", port: "offgas" },
  "e-cdu-lpg": { unit: "CDU", port: "lpg" },
  "e-cdu-naphtha": { unit: "CDU", port: "naphtha" },
  "e-cdu-kero": { unit: "CDU", port: "kerosene" },
  "e-cdu-diesel": { unit: "CDU", port: "diesel" },
  "e-cdu-ago-hc": { unit: "CDU", port: "ago" },
  "e-cdu-ago-fcc": { unit: "CDU", port: "ago" },
  "e-cdu-bottoms": { unit: "CDU", port: "bottoms" },
  "e-vdu-offgas": { unit: "VDU", port: "offgas" },
  "e-vdu-lpg": { unit: "VDU", port: "lpg" },
  "e-vdu-vgo-fcc": { unit: "VDU", port: "vgo" },
  "e-vdu-vgo-hc": { unit: "VDU", port: "vgo" },
  "e-vdu-bottoms": { unit: "VDU", port: "bottoms" },
  "e-fcc-offgas": { unit: "FCC", port: "offgas" },
  "e-fcc-lpg": { unit: "FCC", port: "lpg" },
  "e-fcc-gasoline": { unit: "FCC", port: "gasoline" },
  "e-fcc-lco": { unit: "FCC", port: "lco" },
  "e-hc-offgas": { unit: "HYDROCRACKER", port: "offgas" },
  "e-hc-lpg": { unit: "HYDROCRACKER", port: "lpg" },
  "e-hc-naphtha": { unit: "HYDROCRACKER", port: "naphtha" },
  "e-hc-kero": { unit: "HYDROCRACKER", port: "kerosene" },
  "e-hc-diesel": { unit: "HYDROCRACKER", port: "diesel" },
  "e-coker-offgas": { unit: "COKER", port: "offgas" },
  "e-coker-lpg": { unit: "COKER", port: "lpg" },
  "e-coker-naphtha": { unit: "COKER", port: "naphtha" },
  "e-coker-lco": { unit: "COKER", port: "lco" },
  "e-ccr-offgas": { unit: "CCR", port: "offgas" },
  "e-ccr-lpg": { unit: "CCR", port: "lpg" },
  "e-ccr-reformate": { unit: "CCR", port: "reformate" },
};

function portFlow(
  unitMap: Map<UnitId, SimulationResult["unit_results"][0]>,
  unit: UnitId,
  port: string,
): number | undefined {
  const ur = unitMap.get(unit);
  const out = ur?.outputs[port];
  return out?.total_mt_h;
}

export function applySimulationToPfd(
  nodes: Node[],
  edges: Edge[],
  result: SimulationResult,
): { nodes: Node[]; edges: Edge[] } {
  const unitMap = new Map((result.unit_results ?? []).map((u) => [u.unit, u]));
  const crude = Number(result.diagnostics?.crude_mt_h ?? 0);
  const heaters = result.heaters ?? [];
  const reactorBlocks = result.reactor_blocks ?? [];
  const blenders = result.blenders ?? [];
  const pools = result.pools ?? [];
  const feeders = result.feeders ?? [];

  const nextNodes = nodes.map((n) => {
    const d = { ...(n.data as EquipmentNodeData) };
    d.status = "ok";

    if (UNIT_IDS.includes(n.id as UnitId)) {
      const ur = unitMap.get(n.id as UnitId);
      if (ur) {
        d.subtitle = `${ur.feed_mt_h.toFixed(0)} MT/h feed · ${(ur.utilisation * 100).toFixed(0)}% cap`;
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

    const hr = heaters.find((h) => `h_${h.unit_id}` === n.id);
    if (hr) {
      d.subtitle = `${hr.duty_mw.toFixed(1)} MW fired`;
      return { ...n, data: d };
    }

    if (n.id === "feeder" && feeders[0]) {
      const f = feeders[0];
      d.subtitle = `${f.total_rate_mt_h.toFixed(0)} MT/h · ${f.blended_api.toFixed(1)}° API`;
      return { ...n, data: d };
    }

    if (n.id === "sink_fuel") {
      const off =
        (portFlow(unitMap, "CDU", "offgas") ?? 0) +
        (portFlow(unitMap, "VDU", "offgas") ?? 0) +
        (portFlow(unitMap, "FCC", "offgas") ?? 0);
      d.subtitle = `${off.toFixed(0)} MT/h (plant offgas)`;
      return { ...n, data: d };
    }

    if (n.id === "fcc_riser") {
      const b = reactorBlocks.find((x) => x.block_type === "FCC_RISER_REACTOR");
      if (b) {
        d.subtitle = `Conv ${((b.metrics.conversion_wt ?? 0) * 100).toFixed(0)}% · ${(b.metrics.riser_duty_mw ?? 0).toFixed(1)} MW`;
      }
      return { ...n, data: d };
    }

    if (n.id === "fcc_regen") {
      const b = reactorBlocks.find((x) => x.block_type === "FCC_REGENERATOR");
      if (b) {
        d.subtitle = `${(b.metrics.regen_duty_mw ?? 0).toFixed(1)} MW · flue ${(b.metrics.flue_gas_mt_h ?? 0).toFixed(0)} t/h`;
      }
      return { ...n, data: d };
    }

    if (n.id === "blend_gas") {
      const b = blenders.find((x) => x.blender_id === "bgas");
      if (b) d.subtitle = `${b.rate_mt_h.toFixed(0)} MT/h ${b.specs_met ? "✓ Spec" : "✗ Off spec"}`;
      return { ...n, data: d };
    }

    if (n.id === "blend_diesel") {
      const b = blenders.find((x) => x.blender_id === "bdiesel");
      if (b) d.subtitle = `${b.rate_mt_h.toFixed(0)} MT/h ${b.specs_met ? "✓ Spec" : "✗ Off spec"}`;
      return { ...n, data: d };
    }

    if (n.id.startsWith("pool_")) {
      const pool = n.id.replace("pool_", "");
      const p = pools.find((x) => x.pool === pool);
      if (p) d.subtitle = `${p.total_mt_h.toFixed(0)} MT/h inventory`;
      return { ...n, data: d };
    }

    return { ...n, data: d };
  });

  const flowByEdge: Record<string, number> = {
    "e-feed-cdu": crude,
  };

  for (const [edgeId, spec] of Object.entries(EDGE_PORT)) {
    const f = portFlow(unitMap, spec.unit, spec.port);
    if (f !== undefined) {
      if (edgeId === "e-cdu-ago-hc" || edgeId === "e-cdu-ago-fcc") {
        flowByEdge[edgeId] = f * 0.5;
      } else if (edgeId === "e-vdu-vgo-fcc" || edgeId === "e-vdu-vgo-hc") {
        flowByEdge[edgeId] = f * 0.5;
      } else {
        flowByEdge[edgeId] = f;
      }
    }
  }

  const nextEdges = edges.map((e) => {
    const flow = flowByEdge[e.id];
    if (flow === undefined) return e;
    const data = { ...(e.data as StreamEdgeData), flowMtH: flow };
    return { ...e, data };
  });

  return { nodes: nextNodes, edges: nextEdges };
}
