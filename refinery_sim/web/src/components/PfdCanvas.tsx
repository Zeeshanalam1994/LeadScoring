import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  Panel,
  type Edge,
  type Node,
  type OnNodesChange,
  type OnEdgesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { EquipmentNode } from "../pfd/EquipmentNode";
import { StreamEdge } from "../pfd/StreamEdge";

const nodeTypes = { equipment: EquipmentNode };
const edgeTypes = { stream: StreamEdge };

interface PfdCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onSelectNode: (id: string | null) => void;
  solving: boolean;
}

export function PfdCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onSelectNode,
  solving,
}: PfdCanvasProps) {
  const proOptions = useMemo(() => ({ hideAttribution: true }), []);

  return (
    <div className="pfd-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.35}
        maxZoom={1.8}
        snapToGrid
        snapGrid={[16, 16]}
        proOptions={proOptions}
        defaultEdgeOptions={{
          type: "stream",
          markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#1565c0" },
        }}
        onNodeClick={(_, n) => onSelectNode(n.id)}
        onPaneClick={() => onSelectNode(null)}
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1.2} color="#9aa8b8" />
        <Controls showInteractive={false} className="pfd-controls" />
        <MiniMap
          className="pfd-minimap"
          nodeColor={(n) => {
            const k = (n.data as { kind?: string })?.kind;
            if (k === "column") return "#5c6bc0";
            if (k === "reactor") return "#ef6c00";
            if (k === "tank") return "#2e7d32";
            return "#78909c";
          }}
          maskColor="rgba(200, 210, 220, 0.75)"
        />
        <Panel position="top-left" className="pfd-sheet-label">
          <span>PFD — Refinery Case 1</span>
          {solving && <span className="pfd-solving">Solving…</span>}
        </Panel>
      </ReactFlow>
    </div>
  );
}
