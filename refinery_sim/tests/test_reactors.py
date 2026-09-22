from refinery_sim.core.schema import RefineryConfig
from refinery_sim.core.solver import RefinerySolver
from refinery_sim.core.reactors.fcc_rigorous import fcc_rigorous_train
from refinery_sim.core.components import Stream


def test_fcc_rigorous_couples_riser_and_regenerator():
    feed = Stream.from_dict({"gas_oil": 100.0}, "vgo")
    riser = {"riser_outlet_c": 525, "cat_oil_ratio": 6.0, "preexponential": 5.5, "activation_kj_mol": 22}
    regen = {"regen_dense_bed_c": 720, "excess_air_frac": 0.15, "cat_circulation_mt_h": 1500}
    res = fcc_rigorous_train(feed, riser, regen, {"gasoline_draw_frac": 0.5})
    assert res.conversion_wt > 0.18
    assert res.coke_to_regen_mt_h > 0
    assert res.regen_duty_mw > res.riser_duty_mw * 0.5
    assert res.air_rate_mt_h > 0


def test_solver_returns_reactor_block_results():
    cfg = RefineryConfig.default_config()
    assert cfg.use_rigorous_reactors
    result = RefinerySolver(cfg).solve()
    types = {b.block_type for b in result.reactor_blocks}
    assert "FCC_RISER_REACTOR" in types
    assert "FCC_REGENERATOR" in types
    assert len(result.reactor_blocks) >= 10
