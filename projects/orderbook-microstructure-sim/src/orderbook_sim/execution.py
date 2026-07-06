from __future__ import annotations

from dataclasses import replace
from typing import Dict, List

from .agents import ParentOrderExecutor
from .engine import Engine, SimulationConfig
from .factory import AgentPopulationConfig, build_background_agents, seed_book
from .orderbook import LimitOrderBook, Side


def run_shortfall_trial(
    seed: int,
    pop: AgentPopulationConfig,
    base_config: SimulationConfig,
    entry_time: float,
    strategy: str,
    parent_qty: float,
    side: Side,
    n_slices: int,
    slice_interval: float,
) -> Dict:
    horizon = slice_interval * n_slices + 5.0
    config = replace(base_config, seed=seed, total_time=entry_time + horizon)
    book = LimitOrderBook()
    seed_book(book, config, pop.lp_half_spread, depth_levels=8, size=pop.lp_quote_size)
    agents = build_background_agents(pop, config)
    parent = ParentOrderExecutor(
        agent_id="PARENT",
        side=side,
        total_qty=parent_qty,
        entry_time=entry_time,
        strategy=strategy,
        n_slices=n_slices,
        slice_interval=slice_interval,
    )
    agents.append(parent)
    engine = Engine(config, agents, book)
    engine.run()

    fills = [tr for tr in book.trade_tape if tr.incoming_agent_id == "PARENT"]
    filled_qty = sum(tr.qty for tr in fills)
    vwap = sum(tr.price * tr.qty for tr in fills) / filled_qty if filled_qty > 0 else None
    arrival_mid = parent.arrival_mid
    shortfall_bps = None
    if vwap is not None and arrival_mid:
        side_sign = 1.0 if side is Side.BUY else -1.0
        shortfall_bps = side_sign * (vwap - arrival_mid) / arrival_mid * 1e4

    return {
        "seed": seed,
        "strategy": strategy,
        "entry_time": entry_time,
        "arrival_mid": arrival_mid,
        "vwap": vwap,
        "filled_qty": filled_qty,
        "shortfall_bps": shortfall_bps,
    }


def run_shortfall_experiment(
    seeds: List[int],
    entry_times: List[float],
    pop: AgentPopulationConfig,
    base_config: SimulationConfig,
    parent_qty: float = 60.0,
    side: Side = Side.BUY,
    n_slices: int = 6,
    slice_interval: float = 2.0,
) -> List[Dict]:
    results = []
    for seed in seeds:
        for entry_time in entry_times:
            for strategy in ("aggressive", "twap"):
                results.append(
                    run_shortfall_trial(
                        seed=seed,
                        pop=pop,
                        base_config=base_config,
                        entry_time=entry_time,
                        strategy=strategy,
                        parent_qty=parent_qty,
                        side=side,
                        n_slices=n_slices,
                        slice_interval=slice_interval,
                    )
                )
    return results
