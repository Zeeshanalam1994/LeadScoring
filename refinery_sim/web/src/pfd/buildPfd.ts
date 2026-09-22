import type { Edge, Node } from "@xyflow/react";
import type { EquipmentNodeData, StreamEdgeData } from "./types";

function eq(
  id: string,
  x: number,
  y: number,
  data: EquipmentNodeData,
): Node<EquipmentNodeData> {
  return { id, type: "equipment", position: { x, y }, data };
}

function stream(
  id: string,
  source: string,
  target: string,
  data: StreamEdgeData,
  animated = false,
): Edge<StreamEdgeData> {
  return {
    id,
    source,
    target,
    type: "stream",
    animated,
    data,
  };
}

export function buildInitialPfd(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node<EquipmentNodeData>[] = [
    eq("feeder", 20, 280, {
      kind: "feeder",
      tag: "CRD-1",
      title: "Crude Blend",
      subtitle: "Assay mixer",
    }),
    eq("CDU", 180, 260, { kind: "column", tag: "T-100", title: "CDU", unitId: "CDU" }),
    eq("h_CDU", 180, 380, { kind: "heater", tag: "H-100", title: "Crude Furnace", unitId: "CDU" }),
    eq("VDU", 360, 140, { kind: "column", tag: "T-200", title: "VDU", unitId: "VDU" }),
    eq("h_VDU", 360, 260, { kind: "heater", tag: "H-200", title: "Vacuum Heater", unitId: "VDU" }),
    eq("fcc_riser", 520, 60, { kind: "reactor", tag: "R-300A", title: "FCC Riser", unitId: "fcc_riser" }),
    eq("fcc_regen", 520, 180, { kind: "reactor", tag: "R-300B", title: "Regenerator", unitId: "fcc_regen" }),
    eq("FCC", 680, 120, { kind: "column", tag: "T-300", title: "FCC Frac", unitId: "FCC" }),
    eq("HYDROCRACKER", 520, 320, { kind: "converter", tag: "R-400", title: "Hydrocracker", unitId: "HYDROCRACKER" }),
    eq("COKER", 520, 440, { kind: "converter", tag: "R-500", title: "Delayed Coker", unitId: "COKER" }),
    eq("CCR", 360, 400, { kind: "reactor", tag: "R-600", title: "CCR Train", unitId: "CCR" }),
    eq("pool_lpg", 860, 40, { kind: "tank", tag: "V-LPG", title: "LPG Pool" }),
    eq("pool_gasoline", 860, 130, { kind: "tank", tag: "V-GAS", title: "Gasoline Pool" }),
    eq("blend_gas", 1020, 130, { kind: "blender", tag: "M-GAS", title: "Gasoline Blender" }),
    eq("pool_kerosene", 860, 220, { kind: "tank", tag: "V-JET", title: "Kerosene Pool" }),
    eq("pool_diesel", 860, 310, { kind: "tank", tag: "V-DIE", title: "Diesel Pool" }),
    eq("blend_diesel", 1020, 310, { kind: "blender", tag: "M-DIE", title: "ULSD Blender" }),
  ];

  const edges: Edge<StreamEdgeData>[] = [
    stream("e-feed-cdu", "feeder", "CDU", { streamName: "Crude", phase: "liquid" }, true),
    stream("e-cdu-vdu", "CDU", "VDU", { streamName: "Atm Resid", phase: "liquid" }),
    stream("e-cdu-ccr", "CDU", "CCR", { streamName: "Naphtha", phase: "liquid" }),
    stream("e-vdu-riser", "VDU", "fcc_riser", { streamName: "VGO", phase: "liquid" }),
    stream("e-riser-regen", "fcc_riser", "fcc_regen", { streamName: "Spent Cat", phase: "mixed" }, true),
    stream("e-riser-fcc", "fcc_riser", "FCC", { streamName: "Cracked Vap", phase: "vapor" }),
    stream("e-regen-fcc", "fcc_regen", "fcc_riser", { streamName: "Hot Cat", phase: "utility" }),
    stream("e-vdu-hc", "VDU", "HYDROCRACKER", { streamName: "VGO-S", phase: "liquid" }),
    stream("e-vdu-coker", "VDU", "COKER", { streamName: "VR", phase: "liquid" }),
    stream("e-fcc-gas", "FCC", "pool_gasoline", { streamName: "FCC Gaso", phase: "liquid" }),
    stream("e-gas-blend", "pool_gasoline", "blend_gas", { streamName: "To Blend", phase: "liquid" }),
    stream("e-hc-diesel", "HYDROCRACKER", "pool_diesel", { streamName: "HC Diesel", phase: "liquid" }),
    stream("e-hc-kero", "HYDROCRACKER", "pool_kerosene", { streamName: "HC Kero", phase: "liquid" }),
    stream("e-ccr-gas", "CCR", "pool_gasoline", { streamName: "Reformate", phase: "liquid" }),
    stream("e-cdu-kero", "CDU", "pool_kerosene", { streamName: "Kero Cut", phase: "liquid" }),
    stream("e-cdu-diesel", "CDU", "pool_diesel", { streamName: "AGO", phase: "liquid" }),
    stream("e-die-blend", "pool_diesel", "blend_diesel", { streamName: "To ULSD", phase: "liquid" }),
    stream("e-cdu-h", "CDU", "h_CDU", { streamName: "Heat", phase: "utility" }),
    stream("e-vdu-h", "VDU", "h_VDU", { streamName: "Heat", phase: "utility" }),
  ];

  return { nodes, edges };
}
