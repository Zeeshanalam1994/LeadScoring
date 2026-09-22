import { Handle, Position, type NodeProps } from "@xyflow/react";
import { EquipmentIcon } from "./icons";
import { UNIT_PORTS } from "./unitPorts";
import type { EquipmentNodeData } from "./types";

export function EquipmentNode({ data, selected }: NodeProps) {
  const d = data as EquipmentNodeData;
  const status = d.status ?? "idle";
  const unitKey = typeof d.unitId === "string" ? d.unitId : undefined;
  const ports = d.ports ?? (unitKey ? UNIT_PORTS[unitKey] : undefined);
  const multiPort = ports && ports.length > 0;

  return (
    <div
      className={`eq-node eq-${d.kind} status-${status} ${selected ? "is-selected" : ""} ${
        multiPort ? "eq-node-mult port-count-" + ports.length : ""
      }`}
    >
      <Handle type="target" position={Position.Left} className="eq-handle" />
      <div className="eq-tag">{d.tag}</div>
      <div className="eq-icon-wrap">
        <EquipmentIcon kind={d.kind} size={36} />
      </div>
      <div className="eq-title">{d.title}</div>
      {d.subtitle && <div className="eq-subtitle">{d.subtitle}</div>}
      {multiPort ? (
        ports.map((p) => (
          <Handle
            key={p.id}
            type="source"
            position={Position.Right}
            id={p.id}
            className="eq-handle eq-handle-port"
            style={{ top: `${p.topPct}%` }}
            title={p.label}
          />
        ))
      ) : (
        <Handle type="source" position={Position.Right} className="eq-handle" />
      )}
      {!multiPort && (
        <>
          <Handle type="source" position={Position.Bottom} id="b" className="eq-handle eq-handle-bottom" />
          <Handle type="target" position={Position.Top} id="t" className="eq-handle eq-handle-top" />
        </>
      )}
    </div>
  );
}
