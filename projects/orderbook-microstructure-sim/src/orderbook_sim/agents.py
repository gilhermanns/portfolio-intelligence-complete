from __future__ import annotations

from dataclasses import dataclass, field
from typing import Deque, List, Optional

import numpy as np

from .orderbook import Side


def round_to_tick(price: float, tick: float) -> float:
    return round(round(price / tick) * tick, 10)


class BaseAgent:
    agent_type = "base"

    def __init__(self, agent_id: str, rate: float):
        self.agent_id = agent_id
        self.rate = rate
        self.inventory = 0.0
        self.cash = 0.0
        self.qty_sent = 0.0
        self.qty_filled = 0.0

    def schedule_next(self, rng: np.random.Generator, t_now: float) -> Optional[float]:
        if self.rate <= 0:
            return None
        return t_now + rng.exponential(1.0 / self.rate)

    def act(self, engine, t: float) -> None:
        raise NotImplementedError

    def mark_to_market(self, mid: Optional[float]) -> float:
        if mid is None:
            return self.cash
        return self.cash + self.inventory * mid


class LiquidityProvider(BaseAgent):
    agent_type = "LP"

    def __init__(
        self,
        agent_id: str,
        rate: float,
        half_spread: float,
        quote_size: float,
        inventory_skew: float,
        tick_size: float,
        max_quote_size_mult: float = 3.0,
    ):
        super().__init__(agent_id, rate)
        self.half_spread = half_spread
        self.quote_size = quote_size
        self.inventory_skew = inventory_skew
        self.tick_size = tick_size
        self.max_quote_size_mult = max_quote_size_mult
        self.active_bid_id: Optional[int] = None
        self.active_ask_id: Optional[int] = None
        self.fill_events: List[tuple] = []  # (time, side_held, price)

    def act(self, engine, t: float) -> None:
        book = engine.book
        if self.active_bid_id is not None:
            book.cancel(self.active_bid_id)
            self.active_bid_id = None
        if self.active_ask_id is not None:
            book.cancel(self.active_ask_id)
            self.active_ask_id = None

        ref = book.mid_price if book.mid_price is not None else engine.config.initial_mid_price
        skew = -self.inventory_skew * self.inventory
        bid_price = round_to_tick(ref - self.half_spread + skew, self.tick_size)
        ask_price = round_to_tick(ref + self.half_spread + skew, self.tick_size)
        if bid_price >= ask_price:
            ask_price = round_to_tick(bid_price + self.tick_size, self.tick_size)

        size = self.quote_size
        self.qty_sent += 2 * size
        bid_order, bid_trades = book.add_limit_order(Side.BUY, bid_price, size, t, self.agent_id)
        engine.process_trades(bid_trades, t)
        ask_order, ask_trades = book.add_limit_order(Side.SELL, ask_price, size, t, self.agent_id)
        engine.process_trades(ask_trades, t)

        if bid_order.qty > 1e-12:
            self.active_bid_id = bid_order.order_id
        if ask_order.qty > 1e-12:
            self.active_ask_id = ask_order.order_id


class MomentumTrader(BaseAgent):
    agent_type = "Momentum"

    def __init__(
        self,
        agent_id: str,
        rate: float,
        lookback: float,
        threshold: float,
        order_size: float,
    ):
        super().__init__(agent_id, rate)
        self.lookback = lookback
        self.threshold = threshold
        self.order_size = order_size

    def act(self, engine, t: float) -> None:
        hist = engine.mid_history
        if len(hist) < 2:
            return
        current_mid = hist[-1][1]
        if current_mid is None:
            return
        target_t = t - self.lookback
        past_mid = hist[0][1]
        for ts, m in reversed(hist):
            if ts <= target_t and m is not None:
                past_mid = m
                break
        if past_mid is None or past_mid == 0:
            return
        move = (current_mid - past_mid) / past_mid
        if move >= self.threshold:
            self.qty_sent += self.order_size
            trades, _ = engine.book.market_order(Side.BUY, self.order_size, t, self.agent_id)
            engine.process_trades(trades, t)
        elif move <= -self.threshold:
            self.qty_sent += self.order_size
            trades, _ = engine.book.market_order(Side.SELL, self.order_size, t, self.agent_id)
            engine.process_trades(trades, t)


class NoiseTrader(BaseAgent):
    agent_type = "Noise"

    def __init__(
        self,
        agent_id: str,
        rate: float,
        limit_prob: float,
        size_mean: float,
        offset_std: float,
        tick_size: float,
    ):
        super().__init__(agent_id, rate)
        self.limit_prob = limit_prob
        self.size_mean = size_mean
        self.offset_std = offset_std
        self.tick_size = tick_size

    def act(self, engine, t: float) -> None:
        rng = engine.rng
        book = engine.book
        ref = book.mid_price if book.mid_price is not None else engine.config.initial_mid_price
        side = Side.BUY if rng.random() < 0.5 else Side.SELL
        size = max(1.0, rng.exponential(self.size_mean))
        self.qty_sent += size
        if rng.random() < self.limit_prob:
            offset = abs(rng.normal(0, self.offset_std))
            price = ref - offset if side is Side.BUY else ref + offset
            price = round_to_tick(price, self.tick_size)
            _, trades = book.add_limit_order(side, price, size, t, self.agent_id)
        else:
            trades, _ = book.market_order(side, size, t, self.agent_id)
        engine.process_trades(trades, t)


class PureTaker(BaseAgent):
    """Sends a random-direction aggressive market order on every arrival —
    the 'pure liquidity taking' counterpart used to benchmark the
    liquidity provider's P&L under identical background order flow."""

    agent_type = "PureTaker"

    def __init__(self, agent_id: str, rate: float, order_size: float):
        super().__init__(agent_id, rate)
        self.order_size = order_size

    def act(self, engine, t: float) -> None:
        side = Side.BUY if engine.rng.random() < 0.5 else Side.SELL
        self.qty_sent += self.order_size
        trades, _ = engine.book.market_order(side, self.order_size, t, self.agent_id)
        engine.process_trades(trades, t)


class ParentOrderExecutor(BaseAgent):
    """Injects a large parent order either as one aggressive market order
    or as an equal-sized TWAP slice schedule, alongside ongoing background
    order flow, so implementation shortfall can be measured under realistic
    market impact and replenishment dynamics.
    """

    agent_type = "ParentOrder"

    def __init__(
        self,
        agent_id: str,
        side: Side,
        total_qty: float,
        entry_time: float,
        strategy: str = "aggressive",
        n_slices: int = 1,
        slice_interval: float = 1.0,
    ):
        super().__init__(agent_id, rate=0.0)
        self.side = side
        self.total_qty = total_qty
        self.strategy = strategy
        self.n_slices = 1 if strategy == "aggressive" else n_slices
        self.slice_interval = slice_interval
        self._times = [entry_time + i * slice_interval for i in range(self.n_slices)]
        self._next_idx = 0
        self.arrival_mid: Optional[float] = None

    def schedule_next(self, rng: np.random.Generator, t_now: float) -> Optional[float]:
        if self._next_idx >= len(self._times):
            return None
        return self._times[self._next_idx]

    def act(self, engine, t: float) -> None:
        if self.arrival_mid is None:
            self.arrival_mid = engine.book.mid_price
        slice_qty = self.total_qty / self.n_slices
        self.qty_sent += slice_qty
        trades, _ = engine.book.market_order(self.side, slice_qty, t, self.agent_id)
        engine.process_trades(trades, t)
        self._next_idx += 1
