/** Outlet port layout (percent from top of equipment symbol). */

export interface PortDef {
  id: string;
  label: string;
  topPct: number;
}

export const UNIT_PORTS: Record<string, PortDef[]> = {
  CDU: [
    { id: "offgas", label: "Off Gas", topPct: 5 },
    { id: "lpg", label: "LPG", topPct: 17 },
    { id: "naphtha", label: "Naphtha", topPct: 29 },
    { id: "kero", label: "Kero", topPct: 41 },
    { id: "diesel", label: "Diesel", topPct: 53 },
    { id: "ago", label: "AGO", topPct: 65 },
    { id: "bottoms", label: "Bottoms", topPct: 77 },
  ],
  VDU: [
    { id: "offgas", label: "Off Gas", topPct: 12 },
    { id: "lpg", label: "LPG", topPct: 32 },
    { id: "vgo", label: "VGO", topPct: 52 },
    { id: "bottoms", label: "VR", topPct: 72 },
  ],
  FCC: [
    { id: "offgas", label: "Off Gas", topPct: 10 },
    { id: "lpg", label: "LPG", topPct: 28 },
    { id: "gasoline", label: "Gasoline", topPct: 46 },
    { id: "lco", label: "LCO", topPct: 64 },
    { id: "coke", label: "Coke", topPct: 82 },
  ],
  HYDROCRACKER: [
    { id: "offgas", label: "Off Gas", topPct: 8 },
    { id: "lpg", label: "LPG", topPct: 24 },
    { id: "naphtha", label: "Naphtha", topPct: 40 },
    { id: "kerosene", label: "Kero", topPct: 56 },
    { id: "diesel", label: "Diesel", topPct: 72 },
  ],
  COKER: [
    { id: "offgas", label: "Off Gas", topPct: 8 },
    { id: "lpg", label: "LPG", topPct: 24 },
    { id: "naphtha", label: "Naphtha", topPct: 40 },
    { id: "lco", label: "LCO", topPct: 56 },
    { id: "coke", label: "Coke", topPct: 72 },
  ],
  CCR: [
    { id: "offgas", label: "Off Gas", topPct: 15 },
    { id: "lpg", label: "LPG", topPct: 35 },
    { id: "reformate", label: "Reformate", topPct: 55 },
  ],
};
