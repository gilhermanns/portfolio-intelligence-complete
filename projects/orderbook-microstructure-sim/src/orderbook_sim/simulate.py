from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np

from .agents import PureTaker
from .engine import Engine, SimulationConfig
from .execution import run_shortfall_experiment
from .factory import AgentPopulationConfig, build_background_agents, seed_book
from .metrics import adverse_selection, fill_rates_by_type, realized_volatility
from .orderbook import Side


def run_main_simulation(config: SimulationConfig, pop: AgentPopulationConfig):
    book = None
    from .orderbook import LimitOrderBook

    book = LimitOrderBook()
    seed_book(book, config, pop.lp_half_spread, depth_levels=8, size=pop.lp_quote_size)
    agents = build_background_agents(pop, config)
    pure_taker = PureTaker(agent_id="TAKER_0", rate=pop.momentum_rate, order_size=pop.lp_quote_size)
    agents.append(pure_taker)

    engine = Engine(config, agents, book)
    engine.run()
    return engine, agents, pure_taker


def summarize(engine: Engine, agents, pure_taker) -> Dict:
    sampler = engine.sampler
    book = engine.book
    lp_agents = [a for a in agents if a.agent_type == "LP"]
    lp = lp_agents[0]

    vol = realized_volatility(sampler.mid, engine.config.sampling_dt)
    fill_rates = fill_rates_by_type(engine.agents_by_id)
    adverse = adverse_selection(lp.fill_events, list(engine.mid_history), horizon=5.0)

    final_mid = next((m for m in reversed(sampler.mid) if m is not None), engine.config.initial_mid_price)
    lp_pnl_series = sampler.agent_pnl.get(lp.agent_id, [])
    taker_pnl_series = sampler.agent_pnl.get(pure_taker.agent_id, [])

    spreads = [s for s in sampler.spread if s is not None]
    imbalances = [i for i in sampler.imbalance if i is not None]

    summary = {
        "n_events_sampled": len(sampler.t),
        "n_trades": len(book.trade_tape),
        "final_mid": final_mid,
        "avg_spread": float(np.mean(spreads)) if spreads else None,
        "median_spread": float(np.median(spreads)) if spreads else None,
        "realized_volatility_per_sqrt_time_unit": vol,
        "avg_imbalance": float(np.mean(imbalances)) if imbalances else None,
        "fill_rates_by_type": fill_rates,
        "avg_adverse_selection_per_fill": adverse,
        "lp_final_inventory": lp.inventory,
        "lp_final_pnl": lp_pnl_series[-1] if lp_pnl_series else 0.0,
        "lp_pnl_std": float(np.std(lp_pnl_series)) if lp_pnl_series else 0.0,
        "taker_final_pnl": taker_pnl_series[-1] if taker_pnl_series else 0.0,
        "taker_pnl_std": float(np.std(taker_pnl_series)) if taker_pnl_series else 0.0,
    }
    return summary


def main():
    out_dir = Path(__file__).resolve().parents[2] / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    config = SimulationConfig(total_time=1000.0, seed=42, sampling_dt=0.5)
    pop = AgentPopulationConfig()

    engine, agents, pure_taker = run_main_simulation(config, pop)
    summary = summarize(engine, agents, pure_taker)

    shortfall_results = run_shortfall_experiment(
        seeds=list(range(100, 115)),
        entry_times=[150.0, 400.0, 650.0],
        pop=pop,
        base_config=config,
        parent_qty=60.0,
        side=Side.BUY,
        n_slices=6,
        slice_interval=2.0,
    )

    agg = {}
    for strat in ("aggressive", "twap"):
        vals = [r["shortfall_bps"] for r in shortfall_results if r["strategy"] == strat and r["shortfall_bps"] is not None]
        agg[strat] = {
            "mean_bps": float(np.mean(vals)) if vals else None,
            "std_bps": float(np.std(vals)) if vals else None,
            "n_trials": len(vals),
        }
    summary["execution_shortfall"] = agg

    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    with open(out_dir / "shortfall_trials.json", "w") as f:
        json.dump(shortfall_results, f, indent=2, default=float)

    return engine, agents, pure_taker, summary, shortfall_results


if __name__ == "__main__":
    _, _, _, summary, _ = main()
    print(json.dumps(summary, indent=2, default=float))
