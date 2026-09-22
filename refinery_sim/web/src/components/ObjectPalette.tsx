import { EquipmentIcon } from "../pfd/icons";
import {
  PALETTE_DND_MIME,
  PALETTE_TEMPLATES,
  encodePaletteDrag,
  type PaletteTemplate,
} from "../pfd/paletteDnD";

interface ObjectPaletteProps {
  selectedNodeId: string | null;
  onFocus: (nodeId: string) => void;
}

const FOCUS_MAP: Partial<Record<string, string>> = {
  stream: "feeder",
  cdu: "CDU",
  vdu: "VDU",
  heater: "h_CDU",
  fcc_riser: "fcc_riser",
  fcc_regen: "fcc_regen",
  fcc_frac: "FCC",
  hc: "HYDROCRACKER",
  coker: "COKER",
  ccr: "CCR",
  tank: "pool_gasoline",
  blender: "blend_gas",
};

function onDragStart(e: React.DragEvent, template: PaletteTemplate) {
  e.dataTransfer.setData(PALETTE_DND_MIME, encodePaletteDrag(template.id));
  e.dataTransfer.effectAllowed = "move";
}

export function ObjectPalette({ selectedNodeId, onFocus }: ObjectPaletteProps) {
  return (
    <div className="object-palette">
      <div className="palette-title">Object Palette</div>
      <p className="palette-hint">Drag onto PFD to add</p>
      <div className="palette-grid palette-grid-scroll">
        {PALETTE_TEMPLATES.map((item) => (
          <div
            key={item.id}
            role="button"
            tabIndex={0}
            draggable
            className={`palette-item palette-draggable ${
              FOCUS_MAP[item.id] === selectedNodeId ? "active" : ""
            }`}
            title={`${item.hint} — drag to PFD`}
            onDragStart={(e) => onDragStart(e, item)}
            onClick={() => {
              const target = FOCUS_MAP[item.id];
              if (target) onFocus(target);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                const target = FOCUS_MAP[item.id];
                if (target) onFocus(target);
              }
            }}
          >
            <EquipmentIcon kind={item.kind} size={26} />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
