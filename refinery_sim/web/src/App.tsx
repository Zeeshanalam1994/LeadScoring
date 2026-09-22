import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ReactFlowProvider, useReactFlow, useNodesState, useEdgesState } from "@xyflow/react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PfdCanvas } from "./components/PfdCanvas";
import { ObjectPalette } from "./components/ObjectPalette";
import { StreamTable } from "./components/StreamTable";
import { applySimulationToPfd } from "./pfd/applySimulation";
import { buildInitialPfd } from "./pfd/buildPfd";
import type { HeaterConfig, RefineryConfig, SimulationResult, UnitId, UnitNode } from "./types";

const UNIT_LABELS: Record<UnitId, string> = {
  CDU: "CDU",
  VDU: "VDU",
  FCC: "FCC",
  HYDROCRACKER: "Hydrocracker",
  COKER: "Delayed Coker",
  CCR: "CCR Reformer",
};

const UNIT_PARAM_HINTS: Partial<
  Record<UnitId, { key: string; label: string; min: number; max: number; step: number }[]>
> = {
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

type ConfigTab = "feeders" | "units" | "reactors" | "heaters" | "blenders";
type BottomTab = "streams" | "energy" | "results";

const { nodes: initialNodes, edges: initialEdges } = buildInitialPfd();

function SimulationWorkspace() {
  const { setCenter } = useReactFlow();
  const [config, setConfig] = useState<RefineryConfig | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [configTab, setConfigTab] = useState<ConfigTab>("units");
  const [bottomTab, setBottomTab] = useState<BottomTab>("streams");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>("CDU");
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const nodesRef = useRef(nodes);
  const edgesRef = useRef(edges);
  nodesRef.current = nodes;
  edgesRef.current = edges;

  const loadDefault = useCallback(async () => {
    const res = await fetch("/api/config/default");
    setConfig((await res.json()) as RefineryConfig);
  }, []);

  const runSimulation = useCallback(async () => {
    if (!config) return;
    setLoading(true);
    setError(null);
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "solving" } })));
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as SimulationResult;
      setResult(data);
      const updated = applySimulationToPfd(nodesRef.current, edgesRef.current, data);
      setNodes(updated.nodes);
      setEdges(updated.edges);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
      setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "warn" } })));
    } finally {
      setLoading(false);
    }
  }, [config, setNodes, setEdges]);

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

  const focusNode = (id: string) => {
    const node = nodes.find((n) => n.id === id);
    if (!node) return;
    setSelectedNodeId(id);
    setCenter(node.position.x + 55, node.position.y + 45, { zoom: 1.05, duration: 350 });
  };

  const updateUnit = (id: UnitId, patch: Partial<UnitNode>) => {
    if (!config) return;
    setConfig({ ...config, units: config.units.map((u) => (u.id === id ? { ...u, ...patch } : u)) });
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

  const updateFeederComponent = (feederIdx: number, compIdx: number, rate: number) => {
    if (!config) return;
    const feeders = [...config.feeders];
    const f = { ...feeders[feederIdx], components: [...feeders[feederIdx].components] };
    f.components[compIdx] = { ...f.components[compIdx], rate_mt_h: rate };
    feeders[feederIdx] = f;
    const total = f.components.reduce((s, c) => s + c.rate_mt_h, 0);
    setConfig({ ...config, feeders, crude_rate_mt_h: total });
  };

  const updateHeater = (id: string, patch: Partial<HeaterConfig>) => {
    if (!config) return;
    setConfig({
      ...config,
      heaters: config.heaters.map((h) => (h.id === id ? { ...h, ...patch } : h)),
    });
  };

  if (!config) {
    return <div className="hysys-app" style={{ padding: 24 }}>Loading simulation case…</div>;
  }

  const mb = result?.mass_balance_error_pct ?? 0;
  const converged = mb < 12;

  return (
    <div className="hysys-app">
      <div className="hysys-menubar">
        <span className="brand">RefinerySim</span>
        <span className="menu-item">File</span>
        <span className="menu-item">Edit</span>
        <span className="menu-item">Flowsheets</span>
        <span className="menu-item">Simulation</span>
        <span className="menu-item">Tools</span>
        <span className="spacer" />
        <span className="case-name">Case: Refinery_Main.hsc</span>
      </div>

      <div className="hysys-toolbar">
        <div className="tb-group">
          <button type="button" className="btn btn-run" onClick={runSimulation} disabled={loading}>
            {loading ? "Solving…" : "▶ Solve"}
          </button>
          <button type="button" className="btn btn-secondary" onClick={loadDefault}>Reset</button>
        </div>
        <div className="tb-group">
          <button type="button" className="btn btn-secondary" onClick={() => focusNode("CDU")}>PFD</button>
          <button type="button" className="btn btn-secondary" onClick={() => setBottomTab("streams")}>Streams</button>
        </div>
        {error && <span className="error">{error}</span>}
      </div>

      <div className="hysys-body">
        <ObjectPalette selectedNodeId={selectedNodeId} onFocus={focusNode} />

        <div className="hysys-center">
          <PfdCanvas
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onSelectNode={setSelectedNodeId}
            solving={loading}
          />
        </div>

        <aside className="hysys-workbook">
          <div className="workbook-header">Workbook — Properties</div>
          <div className="props-tree">
            Selected: <span className="sel">{selectedNodeId ?? "—"}</span>
          </div>
          <div className="workbook-tabs">
            {(["feeders", "units", "reactors", "heaters", "blenders"] as ConfigTab[]).map((t) => (
              <button
                key={t}
                type="button"
                className={configTab === t ? "active" : ""}
                onClick={() => setConfigTab(t)}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="workbook-content">
            {configTab === "feeders" && (
              <>
                {config.feeders.map((f, fi) => (
                  <div key={f.id} className="unit-card">
                    <h3>{f.name}</h3>
                    {f.components.map((c, ci) => (
                      <div className="field" key={`${c.assay_id}-${ci}`}>
                        <label>{config.assays.find((a) => a.id === c.assay_id)?.name ?? c.assay_id}</label>
                        <input
                          type="number"
                          value={c.rate_mt_h}
                          onChange={(e) => updateFeederComponent(fi, ci, Number(e.target.value))}
                        />
                      </div>
                    ))}
                  </div>
                ))}
                <div className="field">
                  <label>Flare fraction</label>
                  <input
                    type="number"
                    step={0.005}
                    value={config.flare_fraction}
                    onChange={(e) => setConfig({ ...config, flare_fraction: Number(e.target.value) })}
                  />
                </div>
              </>
            )}
            {configTab === "units" &&
              config.units.map((unit) => (
                <div key={unit.id} className="unit-card">
                  <h3>{UNIT_LABELS[unit.id]}</h3>
                  <label>
                    <input
                      type="checkbox"
                      checked={unit.enabled}
                      onChange={(e) => updateUnit(unit.id, { enabled: e.target.checked })}
                    />
                    Active
                  </label>
                  <div className="field">
                    <label>Capacity MT/h</label>
                    <input
                      type="number"
                      value={unit.capacity_mt_h}
                      onChange={(e) => updateUnit(unit.id, { capacity_mt_h: Number(e.target.value) })}
                    />
                  </div>
                  {(UNIT_PARAM_HINTS[unit.id] ?? []).map((p) => (
                    <div className="field" key={p.key}>
                      <label>{p.label}</label>
                      <input
                        type="number"
                        value={unit.params[p.key] ?? p.min}
                        onChange={(e) => updateUnitParam(unit.id, p.key, Number(e.target.value))}
                      />
                    </div>
                  ))}
                </div>
              ))}
            {configTab === "reactors" && (
              <>
                <label>
                  <input
                    type="checkbox"
                    checked={config.use_rigorous_reactors}
                    onChange={(e) => setConfig({ ...config, use_rigorous_reactors: e.target.checked })}
                  />
                  Rigorous reactor models
                </label>
                {config.reactor_blocks.slice(0, 8).map((block) => (
                  <div key={block.id} className="unit-card">
                    <h3>{block.name}</h3>
                    <div className="metric">{block.host_unit}</div>
                  </div>
                ))}
              </>
            )}
            {configTab === "heaters" &&
              config.heaters.map((h) => (
                <div key={h.id} className="unit-card">
                  <h3>{h.name}</h3>
                  <div className="field">
                    <label>Inlet °C</label>
                    <input
                      type="number"
                      value={h.inlet_c}
                      onChange={(e) => updateHeater(h.id, { inlet_c: Number(e.target.value) })}
                    />
                  </div>
                  <div className="field">
                    <label>Outlet °C</label>
                    <input
                      type="number"
                      value={h.outlet_c}
                      onChange={(e) => updateHeater(h.id, { outlet_c: Number(e.target.value) })}
                    />
                  </div>
                </div>
              ))}
            {configTab === "blenders" &&
              config.blenders.map((b) => (
                <div key={b.id} className="unit-card">
                  <h3>{b.name}</h3>
                  <div className="metric">{b.product} pool</div>
                </div>
              ))}
          </div>
        </aside>
      </div>

      <div className="hysys-bottom">
        <div className="bottom-tabs">
          {(["streams", "energy", "results"] as BottomTab[]).map((t) => (
            <button
              key={t}
              type="button"
              className={bottomTab === t ? "active" : ""}
              onClick={() => setBottomTab(t)}
            >
              {t === "streams" ? "Stream Table" : t === "energy" ? "Energy / Emissions" : "Material Balance"}
            </button>
          ))}
        </div>
        <div className="bottom-pane">
          {bottomTab === "streams" && <StreamTable edges={edges} />}
          {bottomTab === "energy" && result && (
            <div style={{ display: "flex", gap: 24 }}>
              <div>
                <div className="metric">Duty: <strong>{result.energy?.total_duty_mw.toFixed(1)} MW</strong></div>
                <div className="metric">Fuel: <strong>{result.energy?.total_fuel_mt_h.toFixed(1)} MT/h</strong></div>
                <div className="metric">Net steam: <strong>{result.energy?.net_steam_mt_h.toFixed(1)} MT/h</strong></div>
              </div>
              <div>
                <div className="metric">CO₂: <strong>{result.emissions?.co2_total_mt_h.toFixed(1)} MT/h</strong></div>
                <div className="metric">NOₓ: <strong>{result.emissions?.nox_kg_h.toFixed(0)} kg/h</strong></div>
              </div>
              <div className="chart-box" style={{ width: 280 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar dataKey="mt_h" fill="#0066cc" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {bottomTab === "results" && result && (
            <>
              <div className="metric">Mass balance error: <strong>{mb.toFixed(2)}%</strong></div>
              {result.pools.map((p) => (
                <div key={p.pool} className="metric">
                  {p.pool}: <strong>{p.total_mt_h.toFixed(1)} MT/h</strong>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      <div className="hysys-statusbar">
        <span className={converged ? "ok" : "warn"}>
          {converged ? "● Converged" : "● Review balance"}
        </span>
        <span>Crude: {result ? String(result.diagnostics.crude_mt_h) : "—"} MT/h</span>
        <span>Rigorous: {config.use_rigorous_reactors ? "ON" : "OFF"}</span>
        <span>MB: {result ? mb.toFixed(2) : "—"}%</span>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <SimulationWorkspace />
    </ReactFlowProvider>
  );
}
