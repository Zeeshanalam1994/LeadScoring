from refinery_sim.core.schema import RefineryConfig
from refinery_sim.core.solver import RefinerySolver


def test_default_simulation_closes_mass_balance():
    cfg = RefineryConfig.default_config()
    result = RefinerySolver(cfg).solve()
    assert result.mass_balance_error_pct < 15.0
    assert len(result.pools) == 4
    total_pool = sum(p.total_mt_h for p in result.pools)
    assert total_pool > 100.0


def test_disabled_coker_still_runs():
    cfg = RefineryConfig.default_config()
    for u in cfg.units:
        if u.id == "COKER":
            u.enabled = False
    result = RefinerySolver(cfg).solve()
    assert result.mass_balance_error_pct < 20.0
