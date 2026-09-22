import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "@xyflow/react";
import type { StreamEdgeData } from "./types";

export function StreamEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  markerEnd,
}: EdgeProps) {
  const d = (data ?? {}) as StreamEdgeData;
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const phaseClass = d.phase ? `stream-${d.phase}` : "stream-mixed";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        className={`stream-edge ${phaseClass} ${selected ? "is-selected" : ""}`}
      />
      <EdgeLabelRenderer>
        <div
          className={`stream-label ${phaseClass}`}
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
          }}
        >
          <span className="stream-name">{d.streamName}</span>
          {d.flowMtH !== undefined && (
            <span className="stream-flow">{d.flowMtH.toFixed(0)} MT/h</span>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
