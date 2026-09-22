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

type LeftTab = "feeders" | "units" | "heaters" | "blenders";

const initialNodes: Node[] = [
  { id: "feeder", position: { x: -40, y: 170 }, data: { label: "Crude feeder\n(blend)" }, type: "input" },
  { id: "CDU", position: { x: 140, y: 150 }, data: { label: "CDU" } },
  { id: "h_CDU", position: { x: 140, y: 230 }, data: { label: "🔥 Crude furnace" }, style: { fontSize: 10 } },
  { id: "VDU", position: { x: 320, y: 50 }, data: { label: "VDU" } },
  { id: "h_VDU", position: { x: 320, y: 130 }, data: { label: "🔥 Vac heater" }, style: { fontSize: 10 } },
  { id: "FCC", position: { x: 500, y: -10 }, data: { label: "FCC" } },
  { id: "HYDROCRACKER", position: { x: 500, y: 110 }, data: { label: "Hydrocracker" } },
  { id: "COKER", position: { x: 500, y: 230 }, data: { label: "Delayed Coker" } },
  { id: "CCR", position: { x: 320, y: 280 }, data: { label: "CCR" } },
  { id: "pool_lpg", position: { x: 700, y: 10 }, data: { label: "LPG Pool" }, className: "pool-node" },
  { id: "pool_gasoline", position: { x: 700, y: 90 }, data: { label: "Gasoline Pool" }, className: "pool-node" },
  { id: "blend_gas", position: { x: 880, y: 90 }, data: { label: "Gasoline blender" }, className: "pool-node" },
  { id: "pool_kerosene", position: { x: 700, y: 170 }, data: { label: "Kerosene Pool" }, className: "pool-node" },
  { id: "pool_diesel", position: { x: 700, y: 250 }, data: { label: "Diesel Pool" }, className: "pool-node" },
  { id: "blend_diesel", position: { x: 880, y: 250 }, data: { label: "ULSD blender" }, className: "pool-node" },
];

const initialEdges: Edge[] = [
  { id: "e-feed-cdu", source: "feeder", target: "CDU", animated: true },
  { id: "e-cdu-h", source: "CDU", target: "h_CDU", style: { strokeDasharray: "4 4" } },
  { id: "e-cdu-vdu", source: "CDU", target: "VDU" },
  { id: "e-vdu-h", source: "VDU", target: "h_VDU", style: { strokeDasharray: "4 4" } },
  { id: "e-cdu-ccr", source: "CDU", target: "CCR" },
  { id: "e-vdu-fcc", source: "VDU", target: "FCC" },
  { id: "e-vdu-hc", source: "VDU", target: "HYDROCRACKER" },
  { id: "e-vdu-coker", source: "VDU", target: "COKER" },
  { id: "e-fcc-gas", source: "FCC", target: "pool_gasoline" },
  { id: "e-gas-blend", source: "pool_gasoline", target: "blend_gas" },
  { id: "e-die-blend", source: "pool_diesel", target: "blend_diesel" },
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
  const [leftTab, setLeftTab] = useState<LeftTab>("feeders");
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

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
          if (ur) {
            const util = Math.round(ur.utilisation * 100);
            return {
              ...n,
              data: {
                ...n.data,
                label: `${UNIT_LABELS[n.id as UnitId]}\n${ur.feed_mt_h.toFixed(0)} MT/h (${util}%)`,
              },
            };
          }
          const hr = data.heaters.find((h) => `h_${h.unit_id}` === n.id);
          if (hr) {
            return {
              ...n,
              data: { ...n.data, label: `🔥 ${hr.name}\n${hr.duty_mw.toFixed(1)} MW` },
            };
          }
          if (n.id === "blend_gas" && data.blenders[0]) {
            const b = data.blenders.find((x) => x.blender_id === "bgas") ?? data.blenders[0];
            return {
              ...n,
              data: {
                ...n.data,
                label: `${b.name}\n${b.rate_mt_h.toFixed(0)} MT/h ${b.specs_met ? "✓" : "✗"}`,
              },
            };
          }
          if (n.id === "blend_diesel") {
            const b = data.blenders.find((x) => x.blender_id === "bdiesel");
            if (b) {
              return {
                ...n,
                data: {
                  ...n.data,
                  label: `${b.name}\n${b.rate_mt_h.toFixed(0)} MT/h ${b.specs_met ? "✓" : "✗"}`,
                },
              };
            }
          }
          if (n.id === "feeder" && data.feeders[0]) {
            const f = data.feeders[0];
            return {
              ...n,
              data: {
                ...n.data,
                label: `Crude blend\n${f.total_rate_mt_h.toFixed(0)} MT/h · ${f.blended_api.toFixed(1)}°API`,
              },
            };
          }
          return n;
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
    return <div className="app panel">Loading configuration…</div>;
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>Refinery Configuration Simulator</h1>
          <p>Crude blends · heaters · product blenders · energy & emissions</p>
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
        <div className="tabs">
          {(["feeders", "units", "heaters", "blenders"] as LeftTab[]).map((t) => (
            <button
              key={t}
              type="button"
              className={`tab ${leftTab === t ? "active" : ""}`}
              onClick={() => setLeftTab(t)}
            >
              {t}
            </button>
          ))}
        </div>

        {leftTab === "feeders" && (
          <>
            <h2>Crude assays & feeders</h2>
            {config.assays.map((a) => (
              <div key={a.id} className="unit-card">
                <h3>{a.name}</h3>
                <div className="metric">API {a.api} · S {a.sulfur_wt_pct}%</div>
              </div>
            ))}
            {config.feeders.map((f, fi) => (
              <div key={f.id} className="unit-card">
                <header>
                  <h3>{f.name}</h3>
                  <label>
                    <input
                      type="checkbox"
                      checked={f.enabled}
                      onChange={(e) => {
                        const feeders = config.feeders.map((x, i) =>
                          i === fi ? { ...x, enabled: e.target.checked } : x,
                        );
                        setConfig({ ...config, feeders });
                      }}
                    />
                    On
                  </label>
                </header>
                {f.components.map((c, ci) => {
                  const assay = config.assays.find((a) => a.id === c.assay_id);
                  return (
                    <div className="field" key={`${c.assay_id}-${ci}`}>
                      <label>{assay?.name ?? c.assay_id} (MT/h)</label>
                      <input
                        type="number"
                        value={c.rate_mt_h}
                        onChange={(e) => updateFeederComponent(fi, ci, Number(e.target.value))}
                      />
                    </div>
                  );
                })}
              </div>
            ))}
            <div className="field">
              <label>Flare fraction (LPG offgas)</label>
              <input
                type="number"
                step={0.005}
                value={config.flare_fraction}
                onChange={(e) => setConfig({ ...config, flare_fraction: Number(e.target.value) })}
              />
            </div>
          </>
        )}

        {leftTab === "units" &&
          config.units.map((unit) => (
            <div key={unit.id} className="unit-card">
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

        {leftTab === "heaters" &&
          config.heaters.map((h) => (
            <div key={h.id} className="unit-card">
              <header>
                <h3>{h.name}</h3>
                <label>
                  <input
                    type="checkbox"
                    checked={h.enabled}
                    onChange={(e) => updateHeater(h.id, { enabled: e.target.checked })}
                  />
                  On
                </label>
              </header>
              <div className="metric">Unit: {UNIT_LABELS[h.unit_id]}</div>
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
              <div className="field">
                <label>Thermal efficiency</label>
                <input
                  type="number"
                  step={0.01}
                  value={h.thermal_efficiency}
                  onChange={(e) => updateHeater(h.id, { thermal_efficiency: Number(e.target.value) })}
                />
              </div>
            </div>
          ))}

        {leftTab === "blenders" &&
          config.blenders.map((b) => (
            <div key={b.id} className="unit-card">
              <header>
                <h3>{b.name}</h3>
                <label>
                  <input
                    type="checkbox"
                    checked={b.enabled}
                    onChange={(e) => {
                      setConfig({
                        ...config,
                        blenders: config.blenders.map((x) =>
                          x.id === b.id ? { ...x, enabled: e.target.checked } : x,
                        ),
                      });
                    }}
                  />
                  On
                </label>
              </header>
              <div className="metric">Product: {b.product}</div>
              {b.sources.map((s, i) => (
                <div className="metric" key={i}>
                  {s.pool}/{s.tag}: {(s.fraction_of_pool * 100).toFixed(0)}% of tag
                </div>
              ))}
              <div className="metric">
                Spec: RON≥{b.specs.min_ron ?? "—"} · S≤{b.specs.max_sulfur_wt_pct ?? "—"}% · Cetane≥
                {b.specs.min_cetane ?? "—"}
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
        >
          <Background gap={16} color="#2a3a5c" />
          <MiniMap />
          <Controls />
        </ReactFlow>
      </main>

      <aside className="panel">
        <h2>Products & environment</h2>
        {error && <p className="error">{error}</p>}
        {result && (
          <>
            <div className="metric">
              Mass balance error: <strong>{result.mass_balance_error_pct.toFixed(2)}%</strong>
            </div>
            {result.pools.map((p) => (
              <div key={p.pool} className="metric">
                {p.pool}: <strong>{p.total_mt_h.toFixed(1)} MT/h</strong>
                {p.properties.ron ? ` · RON~${p.properties.ron.toFixed(0)}` : ""}
                {p.properties.cetane ? ` · CN~${p.properties.cetane.toFixed(0)}` : ""}
              </div>
            ))}
            <h2 style={{ marginTop: 12 }}>Finished blends</h2>
            {result.blenders.map((b) => (
              <div key={b.blender_id} className="metric">
                {b.name}: <strong>{b.rate_mt_h.toFixed(1)} MT/h</strong>
                <span className={b.specs_met ? "ok" : "error"}> {b.specs_met ? "in spec" : "off spec"}</span>
                {!b.specs_met && b.violations.length > 0 && (
                  <div className="error" style={{ fontSize: "0.75rem" }}>{b.violations.join("; ")}</div>
                )}
              </div>
            ))}
            <h2 style={{ marginTop: 12 }}>Energy & steam</h2>
            {result.energy && (
              <>
                <div className="metric">
                  Fired duty: <strong>{result.energy.total_duty_mw.toFixed(1)} MW</strong>
                </div>
                <div className="metric">
                  Fuel: <strong>{result.energy.total_fuel_mt_h.toFixed(1)} MT/h</strong>
                </div>
                <div className="metric">
                  Steam gen / cons / net:{" "}
                  <strong>
                    {result.energy.steam_generated_mt_h.toFixed(1)} / {result.energy.steam_consumed_mt_h.toFixed(1)} /{" "}
                    {result.energy.net_steam_mt_h.toFixed(1)} MT/h
                  </strong>
                </div>
                <div className="metric">
                  Specific energy: <strong>{result.energy.specific_energy_gj_per_mt_crude.toFixed(2)} GJ/MT crude</strong>
                </div>
              </>
            )}
            <h2 style={{ marginTop: 12 }}>Emissions</h2>
            {result.emissions && (
              <>
                <div className="metric">
                  CO₂ total: <strong>{result.emissions.co2_total_mt_h.toFixed(1)} MT/h</strong> (fuel{" "}
                  {result.emissions.co2_fuel_mt_h.toFixed(1)} + flare {result.emissions.co2_flare_mt_h.toFixed(2)})
                </div>
                <div className="metric">
                  SO₂: <strong>{result.emissions.so2_kg_h.toFixed(0)} kg/h</strong> · NOₓ:{" "}
                  <strong>{result.emissions.nox_kg_h.toFixed(0)} kg/h</strong>
                </div>
                <div className="metric">
                  CO₂ intensity: <strong>{result.emissions.co2_specific_kg_per_mt_crude.toFixed(0)} kg/MT crude</strong>
                </div>
              </>
            )}
            <div className="chart-box" style={{ marginTop: 8 }}>
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
          </>
        )}
      </aside>
    </div>
  );
}

export default App;
