import { EquipmentIcon } from "../pfd/icons";
import type { EquipmentKind } from "../pfd/types";

const PALETTE_ITEMS: { kind: EquipmentKind; label: string; hint: string }[] = [
  { kind: "feeder", label: "Material Stream", hint: "Crude / assay feed" },
  { kind: "column", label: "Distillation", hint: "CDU / VDU / Frac" },
  { kind: "heater", label: "Heater / Furnace", hint: "Fired & process" },
  { kind: "reactor", label: "Reactor", hint: "Riser / CCR / Reform" },
  { kind: "converter", label: "Conversion", hint: "FCC / HC / Coker" },
  { kind: "tank", label: "Tank / Pool", hint: "Product inventory" },
  { kind: "blender", label: "Mixer / Blender", hint: "Spec blending" },
];

interface ObjectPaletteProps {
  selectedNodeId: string | null;
  onFocus: (nodeId: string) => void;
}

const FOCUS_MAP: Record<string, string> = {
  feeder: "feeder",
  column: "CDU",
  heater: "h_CDU",
  reactor: "fcc_riser",
  converter: "HYDROCRACKER",
  tank: "pool_gasoline",
  blender: "blend_gas",
};

export function ObjectPalette({ selectedNodeId, onFocus }: ObjectPaletteProps) {
  return (
    <div className="object-palette">
      <div className="palette-title">Object Palette</div>
      <div className="palette-grid">
        {PALETTE_ITEMS.map((item) => (
          <button
            key={item.kind}
            type="button"
            className={`palette-item ${FOCUS_MAP[item.kind] === selectedNodeId ? "active" : ""}`}
            title={item.hint}
            onClick={() => onFocus(FOCUS_MAP[item.kind])}
          >
            <EquipmentIcon kind={item.kind} size={28} />
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
