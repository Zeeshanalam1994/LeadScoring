import { Handle, Position, type NodeProps } from "@xyflow/react";
import { EquipmentIcon } from "./icons";
import type { EquipmentNodeData } from "./types";

export function EquipmentNode({ data, selected }: NodeProps) {
  const d = data as EquipmentNodeData;
  const status = d.status ?? "idle";

  return (
    <div className={`eq-node eq-${d.kind} status-${status} ${selected ? "is-selected" : ""}`}>
      <Handle type="target" position={Position.Left} className="eq-handle" />
      <div className="eq-tag">{d.tag}</div>
      <div className="eq-icon-wrap">
        <EquipmentIcon kind={d.kind} size={36} />
      </div>
      <div className="eq-title">{d.title}</div>
      {d.subtitle && <div className="eq-subtitle">{d.subtitle}</div>}
      <Handle type="source" position={Position.Right} className="eq-handle" />
      <Handle type="source" position={Position.Bottom} id="b" className="eq-handle eq-handle-bottom" />
      <Handle type="target" position={Position.Top} id="t" className="eq-handle eq-handle-top" />
    </div>
  );
}
