from refinery_sim.core.schema import RefineryConfig
from refinery_sim.core.solver import RefinerySolver
from refinery_sim.core.feeders import blend_assays, default_assay_library


def test_crude_blend_assay():
    lib = default_assay_library()
    blended, props = blend_assays(lib, [("arab_medium", 500), ("heavy_sour", 500)])
    assert blended.api < 31.0
    assert props.sulfur_wt_pct > 2.5


def test_simulation_includes_energy_and_blenders():
    cfg = RefineryConfig.default_config()
    result = RefinerySolver(cfg).solve()
    assert result.energy is not None
    assert result.energy.total_duty_mw > 0
    assert result.emissions is not None
    assert result.emissions.co2_total_mt_h > 0
    assert len(result.feeders) >= 1
    assert len(result.blenders) >= 1
    assert len(result.heaters) >= 4
