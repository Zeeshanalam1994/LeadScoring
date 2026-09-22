export type UnitId = "CDU" | "VDU" | "FCC" | "HYDROCRACKER" | "COKER" | "CCR";
export type PoolId = "lpg" | "kerosene" | "diesel" | "gasoline";

export interface UnitNode {
  id: UnitId;
  enabled: boolean;
  capacity_mt_h: number;
  params: Record<string, number>;
}

export interface RefineryConfig {
  crude_rate_mt_h: number;
  crude_api: number;
  crude_sulfur_wt_pct: number;
  units: UnitNode[];
  routes: unknown[];
}

export interface PoolResult {
  pool: PoolId;
  total_mt_h: number;
  composition: Record<string, number>;
}

export interface UnitResult {
  unit: UnitId;
  feed_mt_h: number;
  utilisation: number;
  outputs: Record<string, { name: string; flows: Record<string, number>; total_mt_h: number }>;
  warnings: string[];
}

export interface SimulationResult {
  mass_balance_error_pct: number;
  unit_results: UnitResult[];
  pools: PoolResult[];
  diagnostics: Record<string, unknown>;
}
