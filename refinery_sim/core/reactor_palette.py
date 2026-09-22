"""Catalog of rigorous reactor block types for the flowsheet palette."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .schema import ReactorBlockType, UnitId


@dataclass(frozen=True)
class PaletteEntry:
    block_type: ReactorBlockType
    display_name: str
    host_unit: UnitId
    description: str
    default_params: Dict[str, float]


PALETTE: List[PaletteEntry] = [
    PaletteEntry(
        "CDU_ATM_COLUMN",
        "Atmospheric distillation column",
        "CDU",
        "Rigorous TBP/stage model with cut draws",
        {"theoretical_stages": 24, "reflux_ratio": 2.5, "pumparound_duty_mw": 15},
    ),
    PaletteEntry(
        "VDU_FLASH_TRAIN",
        "Vacuum flash + VDU column",
        "VDU",
        "Two-stage flash with ejector system anchor",
        {"flash_pressure_kpa": 5, "stages": 14, "draw_vgo_frac": 0.55},
    ),
    PaletteEntry(
        "FCC_RISER_REACTOR",
        "FCC riser reactor",
        "FCC",
        "Fluidized riser cracking with cat/oil ratio and riser ΔT",
        {
            "riser_outlet_c": 520,
            "cat_oil_ratio": 5.5,
            "riser_pressure_kpa": 230,
            "preexponential": 5.5,
            "activation_kj_mol": 22,
        },
    ),
    PaletteEntry(
        "FCC_REGENERATOR",
        "FCC regenerator",
        "FCC",
        "Coke combustion, air rate, flue gas, catalyst reheat",
        {
            "regen_dense_bed_c": 715,
            "excess_air_frac": 0.15,
            "coke_on_cat_wt_pct": 1.0,
            "cat_circulation_mt_h": 1200,
        },
    ),
    PaletteEntry(
        "FCC_FRACTIONATOR",
        "FCC main fractionator",
        "FCC",
        "Gasoline/LCO/HCO separation",
        {"stages": 35, "gasoline_draw_frac": 0.48},
    ),
    PaletteEntry(
        "HC_TRICKLE_BED",
        "Hydrocracker trickle-bed reactor",
        "HYDROCRACKER",
        "Multi-bed with quench — conversion from LHSV and H2 partial pressure",
        {"reactor_temp_c": 385, "pressure_mpa": 15, "lhsv": 1.2, "h2_oil_ratio": 650},
    ),
    PaletteEntry(
        "HC_HIGH_PRESSURE_SEPARATOR",
        "HP separator",
        "HYDROCRACKER",
        "Vapor–liquid split and recycle H2",
        {"separator_temp_c": 85, "separator_pressure_mpa": 14.5},
    ),
    PaletteEntry(
        "COKER_FURNACE",
        "Coker furnace / transfer line",
        "COKER",
        "Thermal soak before coke drums",
        {"outlet_c": 495, "residence_time_min": 2.5},
    ),
    PaletteEntry(
        "COKER_DRUM",
        "Delayed coker drum",
        "COKER",
        "Batch–continuous coke accumulation model",
        {"drum_pressure_kpa": 35, "cycle_fill_frac": 0.85},
    ),
    PaletteEntry(
        "CCR_REACTOR_TRAIN",
        "CCR reactor train",
        "CCR",
        "Series reactors with catalyst circulation and WABT",
        {"wabt_c": 510, "reactor_count": 4, "pressure_mpa": 2.5},
    ),
    PaletteEntry(
        "CCR_STABILIZER",
        "Reformate stabilizer",
        "CCR",
        "Light ends removal from reformate",
        {"stages": 20, "overhead_frac": 0.05},
    ),
    PaletteEntry(
        "HYDROTREATER_FIXED_BED",
        "Fixed-bed hydrotreater",
        "VDU",
        "VGO desulfurization before FCC/HC",
        {"desulfurization_frac": 0.9, "temp_c": 370},
    ),
    PaletteEntry(
        "ISOMERIZATION_REACTOR",
        "Isomerization unit",
        "CCR",
        "Pentane/hexane isom for octane",
        {"conversion_frac": 0.65, "temp_c": 140},
    ),
    PaletteEntry(
        "ALKYLATION_REACTOR",
        "Alkylation reactor",
        "FCC",
        "iC4 + olefins → alkylate",
        {"olefin_conversion": 0.98, "acid_ratio": 1.2},
    ),
    PaletteEntry(
        "DELAYED_COKER_DECOKING",
        "Drum decoking / steam-out",
        "COKER",
        "Decoking cycle utility load",
        {"steam_mt_per_cycle": 120, "cycle_hours": 24},
    ),
]


def palette_by_type() -> Dict[ReactorBlockType, PaletteEntry]:
    return {p.block_type: p for p in PALETTE}


def default_blocks_for_host(host: UnitId) -> List[Tuple[ReactorBlockType, str]]:
    mapping: Dict[UnitId, List[Tuple[ReactorBlockType, str]]] = {
        "CDU": [("CDU_ATM_COLUMN", "cdu_col")],
        "VDU": [("VDU_FLASH_TRAIN", "vdu_flash"), ("HYDROTREATER_FIXED_BED", "vgo_hdt")],
        "FCC": [
            ("FCC_RISER_REACTOR", "fcc_riser"),
            ("FCC_REGENERATOR", "fcc_regen"),
            ("FCC_FRACTIONATOR", "fcc_frac"),
        ],
        "HYDROCRACKER": [("HC_TRICKLE_BED", "hc_rx"), ("HC_HIGH_PRESSURE_SEPARATOR", "hc_sep")],
        "COKER": [("COKER_FURNACE", "coker_furn"), ("COKER_DRUM", "coker_drum"), ("DELAYED_COKER_DECOKING", "coker_decok")],
        "CCR": [("CCR_REACTOR_TRAIN", "ccr_rx"), ("CCR_STABILIZER", "ccr_stab")],
    }
    return mapping.get(host, [])
