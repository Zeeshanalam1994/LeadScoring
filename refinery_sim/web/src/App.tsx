import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RefineryConfig, SimulationResult, UnitId, UnitNode } from "./types";

const UNIT_LABELS: Record<UnitId, string> = {
  CDU: "CDU",
  VDU: "VDU",
  FCC: "FCC",
  HYDROCRACKER: "Hydrocracker",
  COKER: "Delayed Coker",
  CCR: "CCR Reformer",
};

const UNIT_PARAM_HINTS: Partial<Record<UnitId, { key: string; label: string; min: number; max: number; step: number }[]>> = {
  CDU: [{ key: "recovery_eff", label: "Recovery", min: 0.9, max: 1.0, step: 0.001 }],
  VDU: [{ key: "vgo_yield_wt", label: "VGO yield", min: 0.3, max: 0.7, step: 0.01 }],
  FCC: [
    { key: "conversion_wt", label: "Conversion", min: 0.4, max: 0.9, step: 0.01 },
    { key: "feed_share", label: "VGO to FCC", min: 0.1, max: 0.9, step: 0.05 },
  ],
  HYDROCRACKER: [{ key: "conversion_wt", label: "Conversion", min: 0.5, max: 0.98, step: 0.01 }],
  COKER: [{ key: "coke_yield_wt", label: "Coke yield", min: 0.15, max: 0.35, step: 0.01 }],
  CCR: [{ key: "reformate_yield_wt", label: "Reformate yield", min: 0.7, max: 0.9, step: 0.01 }],
};

const initialNodes: Node[] = [
  { id: "crude", position: { x: 0, y: 180 }, data: { label: "Crude Charge" }, type: "input" },
  { id: "CDU", position: { x: 160, y: 160 }, data: { label: "CDU" } },
  { id: "VDU", position: { x: 340, y: 60 }, data: { label: "VDU" } },
  { id: "FCC", position: { x: 520, y: 0 }, data: { label: "FCC" } },
  { id: "HYDROCRACKER", position: { x: 520, y: 120 }, data: { label: "Hydrocracker" } },
  { id: "COKER", position: { x: 520, y: 240 }, data: { label: "Delayed Coker" } },
  { id: "CCR", position: { x: 340, y: 280 }, data: { label: "CCR" } },
  { id: "pool_lpg", position: { x: 720, y: 20 }, data: { label: "LPG Pool" }, className: "pool-node" },
  { id: "pool_gasoline", position: { x: 720, y: 100 }, data: { label: "Gasoline Pool" }, className: "pool-node" },
  { id: "pool_kerosene", position: { x: 720, y: 180 }, data: { label: "Kerosene Pool" }, className: "pool-node" },
  { id: "pool_diesel", position: { x: 720, y: 260 }, data: { label: "Diesel Pool" }, className: "pool-node" },
];

const initialEdges: Edge[] = [
  { id: "e-crude-cdu", source: "crude", target: "CDU", animated: true },
  { id: "e-cdu-vdu", source: "CDU", target: "VDU" },
  { id: "e-cdu-ccr", source: "CDU", target: "CCR" },
  { id: "e-vdu-fcc", source: "VDU", target: "FCC" },
  { id: "e-vdu-hc", source: "VDU", target: "HYDROCRACKER" },
  { id: "e-vdu-coker", source: "VDU", target: "COKER" },
  { id: "e-fcc-gas", source: "FCC", target: "pool_gasoline" },
  { id: "e-fcc-lpg", source: "FCC", target: "pool_lpg" },
  { id: "e-hc-diesel", source: "HYDROCRACKER", target: "pool_diesel" },
  { id: "e-hc-kero", source: "HYDROCRACKER", target: "pool_kerosene" },
  { id: "e-ccr-gas", source: "CCR", target: "pool_gasoline" },
  { id: "e-cdu-kero", source: "CDU", target: "pool_kerosene" },
  { id: "e-cdu-diesel", source: "CDU", target: "pool_diesel" },
];

function App() {
  const [config, setConfig] = useState<RefineryConfig | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);
  const [selectedUnit, setSelectedUnit] = useState<UnitId | null>("CDU");

  const loadDefault = useCallback(async () => {
    const res = await fetch("/api/config/default");
    const data = (await res.json()) as RefineryConfig;
    setConfig(data);
  }, []);

  const runSimulation = useCallback(async () => {
    if (!config) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const data = (await res.json()) as SimulationResult;
      setResult(data);
      setNodes((nds) =>
        nds.map((n) => {
          const ur = data.unit_results.find((u) => u.unit === n.id);
          if (!ur) return n;
          const util = Math.round(ur.utilisation * 100);
          return {
            ...n,
            data: {
              ...n.data,
              label: `${UNIT_LABELS[n.id as UnitId] ?? n.id}\n${ur.feed_mt_h.toFixed(0)} MT/h (${util}%)`,
            },
          };
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }, [config, setNodes]);

  useEffect(() => {
    loadDefault();
  }, [loadDefault]);

  useEffect(() => {
    if (config) runSimulation();
  }, [config, runSimulation]);

  const chartData = useMemo(
    () => result?.pools.map((p) => ({ name: p.pool.toUpperCase(), mt_h: Math.round(p.total_mt_h) })) ?? [],
    [result],
  );

  const updateUnit = (id: UnitId, patch: Partial<UnitNode>) => {
    if (!config) return;
    setConfig({
      ...config,
      units: config.units.map((u) => (u.id === id ? { ...u, ...patch } : u)),
    });
  };

  const updateUnitParam = (id: UnitId, key: string, value: number) => {
    if (!config) return;
    setConfig({
      ...config,
      units: config.units.map((u) =>
        u.id === id ? { ...u, params: { ...u.params, [key]: value } } : u,
      ),
    });
  };

  if (!config) {
    return <div className="app panel">Loading configuration…</div>;
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>Refinery Configuration Simulator</h1>
          <p>First-principles material balance · CDU · VDU · FCC · Hydrocracker · Coker · CCR</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="btn btn-secondary" onClick={loadDefault}>
            Reset
          </button>
          <button type="button" className="btn btn-primary" onClick={runSimulation} disabled={loading}>
            {loading ? "Solving…" : "Run simulation"}
          </button>
        </div>
      </header>

      <aside className="panel">
        <h2>Plant & units</h2>
        <div className="field">
          <label>Crude rate (MT/h)</label>
          <input
            type="number"
            value={config.crude_rate_mt_h}
            onChange={(e) => setConfig({ ...config, crude_rate_mt_h: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>Crude API</label>
          <input
            type="number"
            value={config.crude_api}
            onChange={(e) => setConfig({ ...config, crude_api: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>Sulfur (wt%)</label>
          <input
            type="number"
            value={config.crude_sulfur_wt_pct}
            step={0.1}
            onChange={(e) => setConfig({ ...config, crude_sulfur_wt_pct: Number(e.target.value) })}
          />
        </div>

        {config.units.map((unit) => (
          <div
            key={unit.id}
            className="unit-card"
            style={{ outline: selectedUnit === unit.id ? "1px solid var(--accent)" : "none" }}
            onClick={() => setSelectedUnit(unit.id)}
          >
            <header>
              <h3>{UNIT_LABELS[unit.id]}</h3>
              <label>
                <input
                  type="checkbox"
                  checked={unit.enabled}
                  onChange={(e) => updateUnit(unit.id, { enabled: e.target.checked })}
                />
                On
              </label>
            </header>
            <div className="field">
              <label>Capacity (MT/h)</label>
              <input
                type="number"
                value={unit.capacity_mt_h}
                onChange={(e) => updateUnit(unit.id, { capacity_mt_h: Number(e.target.value) })}
              />
            </div>
            <div className="params">
              {(UNIT_PARAM_HINTS[unit.id] ?? []).map((p) => (
                <div className="field" key={p.key}>
                  <label>{p.label}</label>
                  <input
                    type="number"
                    min={p.min}
                    max={p.max}
                    step={p.step}
                    value={unit.params[p.key] ?? p.min}
                    onChange={(e) => updateUnitParam(unit.id, p.key, Number(e.target.value))}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </aside>

      <main className="panel flow-wrap">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          onNodeClick={(_, node) => {
            if (node.id in UNIT_LABELS) setSelectedUnit(node.id as UnitId);
          }}
        >
          <Background gap={16} color="#2a3a5c" />
          <MiniMap />
          <Controls />
        </ReactFlow>
      </main>

      <aside className="panel">
        <h2>Product pools</h2>
        {error && <p className="error">{error}</p>}
        {result && (
          <>
            <div className="metric">
              Mass balance error: <strong>{result.mass_balance_error_pct.toFixed(2)}%</strong>
            </div>
            <div className="metric">
              Crude charge: <strong>{String(result.diagnostics.crude_mt_h)} MT/h</strong>
            </div>
            <div className="metric">
              Net H₂ (reformer − HC): <strong>{Number(result.diagnostics.h2_net_mt_h).toFixed(1)} MT/h</strong>
            </div>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3a5c" />
                  <XAxis dataKey="name" stroke="#9fb0d0" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#9fb0d0" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="mt_h" fill="#3dd6c6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {result.pools.map((p) => (
              <div key={p.pool} className="metric">
                {p.pool}: <strong>{p.total_mt_h.toFixed(1)} MT/h</strong>
              </div>
            ))}
            <h2 style={{ marginTop: 16 }}>Unit utilisation</h2>
            {result.unit_results.map((u) => (
              <div key={u.unit} className="metric">
                {UNIT_LABELS[u.unit]}: <strong>{(u.utilisation * 100).toFixed(0)}%</strong>
                {u.warnings.length > 0 && <span className="error"> — {u.warnings.join("; ")}</span>}
              </div>
            ))}
          </>
        )}
      </aside>
    </div>
  );
}

export default App;
