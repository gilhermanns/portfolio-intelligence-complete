from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from .orderbook import Side


class MetricsSampler:
    """Fixed-grid sampler treated as just another scheduled agent so the
    engine's single event loop drives both order flow and measurement."""

    agent_type = "sampler"
    agent_id = "sampler"
    rate = 0.0

    def __init__(self, dt: float, depth_levels: int = 5):
        self.dt = dt
        self.depth_levels = depth_levels
        self.t: List[float] = []
        self.mid: List[Optional[float]] = []
        self.spread: List[Optional[float]] = []
        self.bid_depth: List[float] = []
        self.ask_depth: List[float] = []
        self.imbalance: List[Optional[float]] = []
        self.agent_pnl: Dict[str, List[float]] = {}

    def schedule_next(self, rng, t_now: float) -> Optional[float]:
        return t_now + self.dt

    def act(self, engine, t: float) -> None:
        book = engine.book
        d = book.depth(self.depth_levels)
        mid = book.mid_price
        self.t.append(t)
        self.mid.append(mid)
        self.spread.append(book.spread)
        self.bid_depth.append(sum(q for _, q in d["bids"]))
        self.ask_depth.append(sum(q for _, q in d["asks"]))
        self.imbalance.append(book.imbalance(self.depth_levels))
        for agent_id, agent in engine.agents_by_id.items():
            self.agent_pnl.setdefault(agent_id, []).append(agent.mark_to_market(mid))


def realized_volatility(mid_series: List[Optional[float]], sample_dt: float) -> float:
    prices = np.array([m for m in mid_series if m is not None], dtype=float)
    if len(prices) < 3:
        return 0.0
    log_ret = np.diff(np.log(prices))
    per_step_std = log_ret.std(ddof=1)
    steps_per_unit_time = 1.0 / sample_dt
    return float(per_step_std * np.sqrt(steps_per_unit_time))


def fill_rates_by_type(agents_by_id: Dict[str, object]) -> Dict[str, float]:
    totals: Dict[str, List[float]] = {}
    for agent in agents_by_id.values():
        totals.setdefault(agent.agent_type, [0.0, 0.0])
        totals[agent.agent_type][0] += agent.qty_sent
        totals[agent.agent_type][1] += agent.qty_filled
    return {t: (filled / sent if sent > 0 else 0.0) for t, (sent, filled) in totals.items()}


def adverse_selection(
    fill_events: List[tuple], mid_history: List[tuple], horizon: float
) -> Optional[float]:
    if not fill_events:
        return None
    costs = []
    times = [t for t, _ in mid_history]
    mids = [m for _, m in mid_history]
    idx_arr = np.array(times)
    for t, side_held, price in fill_events:
        target = t + horizon
        pos = np.searchsorted(idx_arr, target)
        if pos >= len(mids):
            pos = len(mids) - 1
        future_mid = mids[pos]
        if future_mid is None:
            continue
        if side_held is Side.BUY:
            costs.append(price - future_mid)
        else:
            costs.append(future_mid - price)
    if not costs:
        return None
    return float(np.mean(costs))
