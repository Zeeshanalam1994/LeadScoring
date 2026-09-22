import type { Node } from "@xyflow/react";
import type { UnitId } from "../types";
import type { EquipmentKind, EquipmentNodeData } from "./types";

export const PALETTE_DND_MIME = "application/refinery-palette";

export interface PaletteTemplate {
  id: string;
  kind: EquipmentKind;
  label: string;
  hint: string;
  title: string;
  tagPrefix: string;
  unitId?: UnitId;
}

export const PALETTE_TEMPLATES: PaletteTemplate[] = [
  { id: "stream", kind: "feeder", label: "Stream", hint: "Crude / intermediate", title: "Material Stream", tagPrefix: "STR" },
  { id: "cdu", kind: "column", label: "CDU", hint: "Atmospheric column", title: "CDU", tagPrefix: "T", unitId: "CDU" },
  { id: "vdu", kind: "column", label: "VDU", hint: "Vacuum column", title: "VDU", tagPrefix: "T", unitId: "VDU" },
  { id: "heater", kind: "heater", label: "Heater", hint: "Fired heater", title: "Heater", tagPrefix: "H" },
  { id: "fcc_riser", kind: "reactor", label: "FCC Riser", hint: "Riser reactor", title: "FCC Riser", tagPrefix: "R", unitId: "fcc_riser" },
  { id: "fcc_regen", kind: "reactor", label: "Regenerator", hint: "FCC regenerator", title: "Regenerator", tagPrefix: "R", unitId: "fcc_regen" },
  { id: "fcc_frac", kind: "column", label: "FCC Frac", hint: "Main fractionator", title: "FCC Fractionator", tagPrefix: "T", unitId: "FCC" },
  { id: "hc", kind: "converter", label: "HC Unit", hint: "Hydrocracker", title: "Hydrocracker", tagPrefix: "R", unitId: "HYDROCRACKER" },
  { id: "coker", kind: "converter", label: "Coker", hint: "Delayed coker", title: "Delayed Coker", tagPrefix: "R", unitId: "COKER" },
  { id: "ccr", kind: "reactor", label: "CCR", hint: "Reformer train", title: "CCR", tagPrefix: "R", unitId: "CCR" },
  { id: "tank", kind: "tank", label: "Tank", hint: "Pool / storage", title: "Tank", tagPrefix: "V" },
  { id: "blender", kind: "blender", label: "Blender", hint: "Product blender", title: "Blender", tagPrefix: "M" },
];

const tagSeq: Record<string, number> = {};

export function seedTagCountersFromNodes(nodes: Node[]) {
  for (const n of nodes) {
    const tag = (n.data as EquipmentNodeData)?.tag;
    if (!tag) continue;
    const m = /^([A-Za-z]+)-(\d+)$/.exec(tag);
    if (!m) continue;
    const prefix = m[1];
    const num = Number(m[2]);
    tagSeq[prefix] = Math.max(tagSeq[prefix] ?? 100, num);
  }
}

function nextTag(prefix: string): string {
  const base = tagSeq[prefix] ?? 100;
  const n = base + 1;
  tagSeq[prefix] = n;
  return `${prefix}-${n}`;
}

export function encodePaletteDrag(templateId: string): string {
  return JSON.stringify({ templateId });
}

export function decodePaletteDrag(raw: string): PaletteTemplate | null {
  try {
    const { templateId } = JSON.parse(raw) as { templateId: string };
    return PALETTE_TEMPLATES.find((t) => t.id === templateId) ?? null;
  } catch {
    return null;
  }
}

export function createNodeFromTemplate(
  template: PaletteTemplate,
  position: { x: number; y: number },
): Node<EquipmentNodeData> {
  const id = `usr_${template.id}_${Date.now().toString(36)}`;
  return {
    id,
    type: "equipment",
    position,
    data: {
      kind: template.kind,
      tag: nextTag(template.tagPrefix),
      title: template.title,
      subtitle: "New — connect streams",
      unitId: template.unitId,
      status: "idle",
      userPlaced: true,
    },
  };
}
