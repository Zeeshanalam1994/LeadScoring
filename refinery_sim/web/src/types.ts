export type UnitId = "CDU" | "VDU" | "FCC" | "HYDROCRACKER" | "COKER" | "CCR";
export type PoolId = "lpg" | "kerosene" | "diesel" | "gasoline";

export interface AssayRecord {
  id: string;
  name: string;
  api: number;
  sulfur_wt_pct: number;
  yields: Record<string, number>;
}

export interface FeederComponent {
  assay_id: string;
  rate_mt_h: number;
}

export interface CrudeFeeder {
  id: string;
  name: string;
  enabled: boolean;
  components: FeederComponent[];
}

export interface HeaterConfig {
  id: string;
  unit_id: UnitId;
  name: string;
  enabled: boolean;
  inlet_c: number;
  outlet_c: number;
  cp_kj_kg_k: number;
  thermal_efficiency: number;
  fuel_lhv_mj_kg: number;
  steam_generation_frac: number;
}

export interface ProductBlender {
  id: string;
  name: string;
  product: PoolId;
  enabled: boolean;
  sources: { pool: PoolId; tag: string; fraction_of_pool: number }[];
  specs: {
    min_ron?: number;
    max_ron?: number;
    min_cetane?: number;
    max_sulfur_wt_pct?: number;
  };
}

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
  flare_fraction: number;
  assays: AssayRecord[];
  feeders: CrudeFeeder[];
  heaters: HeaterConfig[];
  blenders: ProductBlender[];
  units: UnitNode[];
  routes: unknown[];
}

export interface PoolResult {
  pool: PoolId;
  total_mt_h: number;
  composition: Record<string, number>;
  properties: Record<string, number>;
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
  feeders: {
    feeder_id: string;
    name: string;
    total_rate_mt_h: number;
    blended_api: number;
    blended_sulfur_wt_pct: number;
  }[];
  blenders: {
    blender_id: string;
    name: string;
    product: PoolId;
    rate_mt_h: number;
    properties: Record<string, number>;
    specs_met: boolean;
    violations: string[];
  }[];
  heaters: {
    id: string;
    unit_id: UnitId;
    name: string;
    duty_mw: number;
    fuel_mt_h: number;
    steam_generated_mt_h: number;
    co2_mt_h: number;
  }[];
  energy?: {
    total_duty_mw: number;
    total_fuel_mt_h: number;
    steam_generated_mt_h: number;
    steam_consumed_mt_h: number;
    net_steam_mt_h: number;
    specific_energy_gj_per_mt_crude: number;
  };
  emissions?: {
    co2_total_mt_h: number;
    co2_fuel_mt_h: number;
    co2_flare_mt_h: number;
    so2_kg_h: number;
    nox_kg_h: number;
    co2_specific_kg_per_mt_crude: number;
  };
  diagnostics: Record<string, unknown>;
}
