import type { UnitId } from "../types";

export type EquipmentKind =
  | "feeder"
  | "column"
  | "heater"
  | "reactor"
  | "converter"
  | "tank"
  | "blender"
  | "mixer";

export interface EquipmentNodeData {
  kind: EquipmentKind;
  tag: string;
  title: string;
  subtitle?: string;
  unitId?: UnitId | string;
  status?: "idle" | "ok" | "warn" | "solving";
  [key: string]: unknown;
}

export interface StreamEdgeData {
  streamName: string;
  flowMtH?: number;
  phase?: "liquid" | "vapor" | "mixed" | "utility";
}
