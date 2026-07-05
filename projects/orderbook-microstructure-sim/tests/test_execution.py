from orderbook_sim.engine import SimulationConfig
from orderbook_sim.execution import run_shortfall_experiment, run_shortfall_trial
from orderbook_sim.factory import AgentPopulationConfig
from orderbook_sim.orderbook import Side


def _pop_and_config():
    pop = AgentPopulationConfig(n_lp=1, n_momentum=2, n_noise=4)
    config = SimulationConfig(total_time=50.0, sampling_dt=1.0)
    return pop, config


def test_aggressive_trial_fills_full_quantity_immediately():
    pop, config = _pop_and_config()
    result = run_shortfall_trial(
        seed=11,
        pop=pop,
        base_config=config,
        entry_time=20.0,
        strategy="aggressive",
        parent_qty=20.0,
        side=Side.BUY,
        n_slices=1,
        slice_interval=1.0,
    )
    assert result["arrival_mid"] is not None
    assert result["filled_qty"] == 20.0
    assert result["vwap"] is not None
    assert result["shortfall_bps"] is not None


def test_buy_aggressive_shortfall_is_non_negative_on_average():
    # An aggressive buy walks the ask side, so VWAP should be >= arrival mid,
    # i.e. non-negative implementation shortfall in expectation.
    pop, config = _pop_and_config()
    shortfalls = []
    for seed in range(300, 306):
        result = run_shortfall_trial(
            seed=seed,
            pop=pop,
            base_config=config,
            entry_time=20.0,
            strategy="aggressive",
            parent_qty=15.0,
            side=Side.BUY,
            n_slices=1,
            slice_interval=1.0,
        )
        if result["shortfall_bps"] is not None:
            shortfalls.append(result["shortfall_bps"])
    assert len(shortfalls) > 0
    assert sum(shortfalls) / len(shortfalls) >= 0


def test_twap_trial_slices_across_multiple_times():
    pop, config = _pop_and_config()
    result = run_shortfall_trial(
        seed=42,
        pop=pop,
        base_config=config,
        entry_time=10.0,
        strategy="twap",
        parent_qty=18.0,
        side=Side.SELL,
        n_slices=3,
        slice_interval=2.0,
    )
    assert result["filled_qty"] == 18.0


def test_shortfall_experiment_produces_both_strategies():
    pop, config = _pop_and_config()
    results = run_shortfall_experiment(
        seeds=[1, 2],
        entry_times=[15.0],
        pop=pop,
        base_config=config,
        parent_qty=12.0,
        side=Side.BUY,
        n_slices=2,
        slice_interval=1.0,
    )
    strategies = {r["strategy"] for r in results}
    assert strategies == {"aggressive", "twap"}
    assert len(results) == 4
