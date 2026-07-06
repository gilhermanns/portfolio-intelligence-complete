from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from itertools import count
from typing import Deque, Dict, List, Optional

from sortedcontainers import SortedList


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    order_id: int
    side: Side
    price: float
    qty: float
    original_qty: float
    timestamp: float
    agent_id: str


@dataclass
class Trade:
    timestamp: float
    price: float
    qty: float
    aggressor_side: Side
    resting_order_id: int
    incoming_order_id: Optional[int]
    resting_agent_id: str
    incoming_agent_id: str


class LimitOrderBook:
    """Price-time priority limit order book for a single instrument.

    Resting orders at the same price fill FIFO by arrival order (a plain
    ``deque`` per price level). Cancellation removes the exact order object
    from its level directly (O(level size), which stays tiny at simulated
    order-flow rates) rather than lazy-deleting, so the book never carries
    stale quantity that would distort depth/imbalance snapshots.
    """

    def __init__(self) -> None:
        self._bid_prices: SortedList = SortedList()
        self._ask_prices: SortedList = SortedList()
        self.bids: Dict[float, Deque[Order]] = {}
        self.asks: Dict[float, Deque[Order]] = {}
        self._order_index: Dict[int, Order] = {}
        self._id_counter = count(1)
        self.trade_tape: List[Trade] = []

    def new_order_id(self) -> int:
        return next(self._id_counter)

    @property
    def best_bid(self) -> Optional[float]:
        return self._bid_prices[-1] if self._bid_prices else None

    @property
    def best_ask(self) -> Optional[float]:
        return self._ask_prices[0] if self._ask_prices else None

    @property
    def mid_price(self) -> Optional[float]:
        bb, ba = self.best_bid, self.best_ask
        if bb is None or ba is None:
            return None
        return (bb + ba) / 2.0

    @property
    def spread(self) -> Optional[float]:
        bb, ba = self.best_bid, self.best_ask
        if bb is None or ba is None:
            return None
        return ba - bb

    def depth(self, levels: int = 5) -> Dict[str, List[tuple]]:
        bid_levels = list(reversed(self._bid_prices))[:levels]
        ask_levels = list(self._ask_prices)[:levels]
        bid_book = [(p, sum(o.qty for o in self.bids[p])) for p in bid_levels]
        ask_book = [(p, sum(o.qty for o in self.asks[p])) for p in ask_levels]
        return {"bids": bid_book, "asks": ask_book}

    def imbalance(self, levels: int = 5) -> Optional[float]:
        d = self.depth(levels)
        bid_qty = sum(q for _, q in d["bids"])
        ask_qty = sum(q for _, q in d["asks"])
        total = bid_qty + ask_qty
        if total == 0:
            return None
        return (bid_qty - ask_qty) / total

    def _book_side(self, side: Side):
        return (self.bids, self._bid_prices) if side is Side.BUY else (self.asks, self._ask_prices)

    def _opposite_side(self, side: Side):
        return (self.asks, self._ask_prices) if side is Side.BUY else (self.bids, self._bid_prices)

    def cancel(self, order_id: int) -> bool:
        order = self._order_index.pop(order_id, None)
        if order is None:
            return False
        book, prices = self._book_side(order.side)
        level = book[order.price]
        level.remove(order)
        if not level:
            del book[order.price]
            prices.remove(order.price)
        return True

    def _crosses(self, side: Side, price: Optional[float], best_opp: Optional[float]) -> bool:
        if best_opp is None:
            return False
        if price is None:
            return True
        return price >= best_opp if side is Side.BUY else price <= best_opp

    def _match(
        self,
        side: Side,
        qty: float,
        price: Optional[float],
        timestamp: float,
        agent_id: str,
        incoming_order_id: Optional[int],
    ) -> tuple[List[Trade], float]:
        book, prices = self._opposite_side(side)
        trades: List[Trade] = []
        remaining = qty
        while remaining > 1e-12:
            if not prices:
                break
            best_opp = prices[0] if side is Side.BUY else prices[-1]
            if not self._crosses(side, price, best_opp):
                break
            level = book[best_opp]
            while level and remaining > 1e-12:
                resting = level[0]
                fill_qty = min(remaining, resting.qty)
                trades.append(
                    Trade(
                        timestamp=timestamp,
                        price=best_opp,
                        qty=fill_qty,
                        aggressor_side=side,
                        resting_order_id=resting.order_id,
                        incoming_order_id=incoming_order_id,
                        resting_agent_id=resting.agent_id,
                        incoming_agent_id=agent_id,
                    )
                )
                resting.qty -= fill_qty
                remaining -= fill_qty
                if resting.qty <= 1e-12:
                    level.popleft()
                    del self._order_index[resting.order_id]
            if not level:
                del book[best_opp]
                prices.remove(best_opp)
        self.trade_tape.extend(trades)
        return trades, remaining

    def add_limit_order(
        self, side: Side, price: float, qty: float, timestamp: float, agent_id: str
    ) -> tuple[Order, List[Trade]]:
        order_id = self.new_order_id()
        trades, remaining = self._match(side, qty, price, timestamp, agent_id, order_id)
        order = Order(order_id, side, price, remaining, qty, timestamp, agent_id)
        if remaining > 1e-12:
            book, prices = self._book_side(side)
            if price not in book:
                book[price] = deque()
                prices.add(price)
            book[price].append(order)
            self._order_index[order_id] = order
        return order, trades

    def market_order(
        self, side: Side, qty: float, timestamp: float, agent_id: str
    ) -> tuple[List[Trade], float]:
        return self._match(side, qty, None, timestamp, agent_id, None)
