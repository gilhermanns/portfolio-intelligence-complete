from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from itertools import count
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

from .agents import LiquidityProvider
from .metrics import MetricsSampler
from .orderbook import LimitOrderBook, Side, Trade


@dataclass
class SimulationConfig:
    total_time: float = 500.0
    tick_size: float = 0.01
    initial_mid_price: float = 100.0
    seed: int = 7
    sampling_dt: float = 0.5
    mid_history_maxlen: int = 20000


class Engine:
    def __init__(self, config: SimulationConfig, agents: List, book: Optional[LimitOrderBook] = None):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.book = book if book is not None else LimitOrderBook()
        self.agents = list(agents)
        self.agents_by_id = {a.agent_id: a for a in self.agents}
        self.sampler = MetricsSampler(config.sampling_dt)
        self.mid_history: Deque[Tuple[float, Optional[float]]] = deque(
            maxlen=config.mid_history_maxlen
        )
        self._seq = count()
        self._heap: List[Tuple[float, int, object]] = []
        self.clock = 0.0

    def process_trades(self, trades: List[Trade], t: float) -> None:
        for tr in trades:
            resting = self.agents_by_id.get(tr.resting_agent_id)
            aggressor = self.agents_by_id.get(tr.incoming_agent_id)
            resting_side = Side.SELL if tr.aggressor_side is Side.BUY else Side.BUY
            if resting is not None:
                if resting_side is Side.BUY:
                    resting.inventory += tr.qty
                    resting.cash -= tr.qty * tr.price
                else:
                    resting.inventory -= tr.qty
                    resting.cash += tr.qty * tr.price
                resting.qty_filled += tr.qty
                if isinstance(resting, LiquidityProvider):
                    resting.fill_events.append((t, resting_side, tr.price))
            if aggressor is not None:
                if tr.aggressor_side is Side.BUY:
                    aggressor.inventory += tr.qty
                    aggressor.cash -= tr.qty * tr.price
                else:
                    aggressor.inventory -= tr.qty
                    aggressor.cash += tr.qty * tr.price
                aggressor.qty_filled += tr.qty

    def _push(self, t: float, agent) -> None:
        heapq.heappush(self._heap, (t, next(self._seq), agent))

    def run(self) -> None:
        for agent in self.agents:
            t0 = agent.schedule_next(self.rng, 0.0)
            if t0 is not None and t0 <= self.config.total_time:
                self._push(t0, agent)
        t0 = self.sampler.schedule_next(self.rng, 0.0)
        self._push(t0, self.sampler)

        while self._heap:
            t, _, actor = heapq.heappop(self._heap)
            if t > self.config.total_time:
                continue
            self.clock = t
            actor.act(self, t)
            self.mid_history.append((t, self.book.mid_price))
            nxt = actor.schedule_next(self.rng, t)
            if nxt is not None and nxt <= self.config.total_time:
                self._push(nxt, actor)
