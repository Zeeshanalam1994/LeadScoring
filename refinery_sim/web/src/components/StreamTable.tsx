import type { Edge } from "@xyflow/react";
import type { StreamEdgeData } from "../pfd/types";

export function StreamTable({ edges }: { edges: Edge[] }) {
  const rows = edges
    .filter((e) => e.type === "stream")
    .map((e) => {
      const d = (e.data ?? {}) as StreamEdgeData;
      return {
        id: e.id,
        name: d.streamName,
        from: e.source,
        to: e.target,
        flow: d.flowMtH,
        phase: d.phase ?? "mixed",
      };
    });

  return (
    <div className="stream-table-wrap">
      <table className="stream-table">
        <thead>
          <tr>
            <th>Stream</th>
            <th>From</th>
            <th>To</th>
            <th>Phase</th>
            <th>Mass flow (MT/h)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.name}</td>
              <td>{r.from}</td>
              <td>{r.to}</td>
              <td>{r.phase}</td>
              <td className="num">{r.flow !== undefined ? r.flow.toFixed(1) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
