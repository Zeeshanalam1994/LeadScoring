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
  sourceHandle?: string,
  targetHandle?: string,
  animated = false,
): Edge<StreamEdgeData> {
  return {
    id,
    source,
    target,
    sourceHandle,
    targetHandle,
    type: "stream",
    animated,
    data,
  };
}

export function buildInitialPfd(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node<EquipmentNodeData>[] = [
    eq("feeder", 0, 320, {
      kind: "feeder",
      tag: "CRD-1",
      title: "Crude Blend",
      subtitle: "Assay mixer",
    }),
    eq("CDU", 160, 40, { kind: "column", tag: "T-100", title: "CDU", unitId: "CDU" }),
    eq("h_CDU", 160, 340, { kind: "heater", tag: "H-100", title: "Crude Furnace", unitId: "CDU" }),
    eq("VDU", 380, 120, { kind: "column", tag: "T-200", title: "VDU", unitId: "VDU" }),
    eq("h_VDU", 380, 340, { kind: "heater", tag: "H-200", title: "Vacuum Heater", unitId: "VDU" }),
    eq("fcc_riser", 560, 40, { kind: "reactor", tag: "R-300A", title: "FCC Riser", unitId: "fcc_riser" }),
    eq("fcc_regen", 560, 160, { kind: "reactor", tag: "R-300B", title: "Regenerator", unitId: "fcc_regen" }),
    eq("FCC", 720, 80, { kind: "column", tag: "T-300", title: "FCC Frac", unitId: "FCC" }),
    eq("HYDROCRACKER", 560, 280, { kind: "converter", tag: "R-400", title: "Hydrocracker", unitId: "HYDROCRACKER" }),
    eq("COKER", 560, 420, { kind: "converter", tag: "R-500", title: "Delayed Coker", unitId: "COKER" }),
    eq("CCR", 380, 420, { kind: "reactor", tag: "R-600", title: "CCR Train", unitId: "CCR" }),
    eq("sink_fuel", 920, 20, { kind: "tank", tag: "FUEL", title: "Fuel Gas" }),
    eq("pool_lpg", 920, 100, { kind: "tank", tag: "V-LPG", title: "LPG Pool" }),
    eq("pool_gasoline", 920, 200, { kind: "tank", tag: "V-GAS", title: "Gasoline Pool" }),
    eq("blend_gas", 1080, 200, { kind: "blender", tag: "M-GAS", title: "Gasoline Blender" }),
    eq("pool_kerosene", 920, 300, { kind: "tank", tag: "V-JET", title: "Kerosene Pool" }),
    eq("pool_diesel", 920, 400, { kind: "tank", tag: "V-DIE", title: "Diesel Pool" }),
    eq("blend_diesel", 1080, 400, { kind: "blender", tag: "M-DIE", title: "ULSD Blender" }),
  ];

  const edges: Edge<StreamEdgeData>[] = [
    stream("e-feed-cdu", "feeder", "CDU", { streamName: "Crude", phase: "liquid" }, undefined, undefined, true),

    // CDU — seven cuts
    stream("e-cdu-offgas", "CDU", "sink_fuel", { streamName: "Off Gas", phase: "vapor" }, "offgas"),
    stream("e-cdu-lpg", "CDU", "pool_lpg", { streamName: "LPG", phase: "mixed" }, "lpg"),
    stream("e-cdu-naphtha", "CDU", "CCR", { streamName: "Naphtha", phase: "liquid" }, "naphtha"),
    stream("e-cdu-kero", "CDU", "pool_kerosene", { streamName: "Kerosene", phase: "liquid" }, "kero"),
    stream("e-cdu-diesel", "CDU", "pool_diesel", { streamName: "Diesel", phase: "liquid" }, "diesel"),
    stream("e-cdu-ago-hc", "CDU", "HYDROCRACKER", { streamName: "AGO", phase: "liquid" }, "ago"),
    stream("e-cdu-ago-fcc", "CDU", "fcc_riser", { streamName: "AGO", phase: "liquid" }, "ago"),
    stream("e-cdu-bottoms", "CDU", "VDU", { streamName: "Atm Bottoms", phase: "liquid" }, "bottoms"),

    // VDU
    stream("e-vdu-offgas", "VDU", "sink_fuel", { streamName: "Vac Off Gas", phase: "vapor" }, "offgas"),
    stream("e-vdu-lpg", "VDU", "pool_lpg", { streamName: "Vac LPG", phase: "mixed" }, "lpg"),
    stream("e-vdu-vgo-fcc", "VDU", "fcc_riser", { streamName: "VGO", phase: "liquid" }, "vgo"),
    stream("e-vdu-vgo-hc", "VDU", "HYDROCRACKER", { streamName: "VGO", phase: "liquid" }, "vgo"),
    stream("e-vdu-bottoms", "VDU", "COKER", { streamName: "Vac Resid", phase: "liquid" }, "bottoms"),

    stream("e-riser-regen", "fcc_riser", "fcc_regen", { streamName: "Spent Cat", phase: "mixed" }, undefined, undefined, true),
    stream("e-riser-fcc", "fcc_riser", "FCC", { streamName: "Reactor Vap", phase: "vapor" }),
    stream("e-regen-riser", "fcc_regen", "fcc_riser", { streamName: "Hot Cat", phase: "utility" }),

    stream("e-fcc-offgas", "FCC", "sink_fuel", { streamName: "FCC Off Gas", phase: "vapor" }, "offgas"),
    stream("e-fcc-lpg", "FCC", "pool_lpg", { streamName: "FCC LPG", phase: "mixed" }, "lpg"),
    stream("e-fcc-gasoline", "FCC", "pool_gasoline", { streamName: "FCC Gasoline", phase: "liquid" }, "gasoline"),
    stream("e-fcc-lco", "FCC", "pool_diesel", { streamName: "LCO", phase: "liquid" }, "lco"),
    stream("e-fcc-coke", "FCC", "fcc_regen", { streamName: "Coke", phase: "utility" }, "coke"),

    stream("e-hc-offgas", "HYDROCRACKER", "sink_fuel", { streamName: "HC Off Gas", phase: "vapor" }, "offgas"),
    stream("e-hc-lpg", "HYDROCRACKER", "pool_lpg", { streamName: "HC LPG", phase: "mixed" }, "lpg"),
    stream("e-hc-naphtha", "HYDROCRACKER", "pool_gasoline", { streamName: "HC Naphtha", phase: "liquid" }, "naphtha"),
    stream("e-hc-kero", "HYDROCRACKER", "pool_kerosene", { streamName: "HC Kero", phase: "liquid" }, "kerosene"),
    stream("e-hc-diesel", "HYDROCRACKER", "pool_diesel", { streamName: "HC Diesel", phase: "liquid" }, "diesel"),

    stream("e-coker-offgas", "COKER", "sink_fuel", { streamName: "Coker Off Gas", phase: "vapor" }, "offgas"),
    stream("e-coker-lpg", "COKER", "pool_lpg", { streamName: "Coker LPG", phase: "mixed" }, "lpg"),
    stream("e-coker-naphtha", "COKER", "pool_gasoline", { streamName: "Coker Naphtha", phase: "liquid" }, "naphtha"),
    stream("e-coker-lco", "COKER", "pool_diesel", { streamName: "Coker LCO", phase: "liquid" }, "lco"),

    stream("e-ccr-offgas", "CCR", "sink_fuel", { streamName: "CCR Off Gas", phase: "vapor" }, "offgas"),
    stream("e-ccr-lpg", "CCR", "pool_lpg", { streamName: "CCR LPG", phase: "mixed" }, "lpg"),
    stream("e-ccr-reformate", "CCR", "pool_gasoline", { streamName: "Reformate", phase: "liquid" }, "reformate"),

    stream("e-gas-blend", "pool_gasoline", "blend_gas", { streamName: "To Blend", phase: "liquid" }),
    stream("e-die-blend", "pool_diesel", "blend_diesel", { streamName: "To ULSD", phase: "liquid" }),
    stream("e-cdu-h", "CDU", "h_CDU", { streamName: "Heat", phase: "utility" }),
    stream("e-vdu-h", "VDU", "h_VDU", { streamName: "Heat", phase: "utility" }),
  ];

  return { nodes, edges };
}
