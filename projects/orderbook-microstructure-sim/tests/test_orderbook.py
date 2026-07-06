import pytest

from orderbook_sim.orderbook import LimitOrderBook, Side


def test_add_limit_order_rests_when_no_cross():
    book = LimitOrderBook()
    order, trades = book.add_limit_order(Side.BUY, 99.0, 10, 0.0, "A")
    assert trades == []
    assert order.qty == 10
    assert book.best_bid == 99.0
    assert book.best_ask is None


def test_best_bid_ask_and_mid_spread():
    book = LimitOrderBook()
    book.add_limit_order(Side.BUY, 99.0, 5, 0.0, "A")
    book.add_limit_order(Side.BUY, 99.5, 5, 0.0, "B")
    book.add_limit_order(Side.SELL, 100.5, 5, 0.0, "C")
    book.add_limit_order(Side.SELL, 101.0, 5, 0.0, "D")
    assert book.best_bid == 99.5
    assert book.best_ask == 100.5
    assert book.mid_price == pytest.approx(100.0)
    assert book.spread == pytest.approx(1.0)


def test_crossing_limit_order_matches_price_time_priority():
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 100.0, 5, 0.0, "S1")
    book.add_limit_order(Side.SELL, 100.0, 5, 1.0, "S2")
    order, trades = book.add_limit_order(Side.BUY, 100.0, 7, 2.0, "B1")

    assert len(trades) == 2
    assert trades[0].resting_agent_id == "S1"
    assert trades[0].qty == 5
    assert trades[1].resting_agent_id == "S2"
    assert trades[1].qty == 2
    assert order.qty == 0
    remaining = book.asks[100.0]
    assert len(remaining) == 1
    assert remaining[0].agent_id == "S2"
    assert remaining[0].qty == 3


def test_fifo_at_same_price_level():
    book = LimitOrderBook()
    book.add_limit_order(Side.BUY, 100.0, 4, 0.0, "first")
    book.add_limit_order(Side.BUY, 100.0, 4, 1.0, "second")
    trades, _ = book.market_order(Side.SELL, 5, 2.0, "taker")
    assert trades[0].resting_agent_id != trades[1].resting_agent_id
    first_trade = [t for t in trades if t.qty == 4][0]
    assert first_trade.resting_agent_id == "first"
    remaining_level = book.bids[100.0]
    assert len(remaining_level) == 1
    assert remaining_level[0].agent_id == "second"
    assert remaining_level[0].qty == 3


def test_partial_fill_leaves_correct_remainder():
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 101.0, 10, 0.0, "maker")
    trades, remaining = book.market_order(Side.BUY, 4, 1.0, "taker")
    assert remaining == 0
    assert trades[0].qty == 4
    level = book.asks[101.0]
    assert len(level) == 1
    assert level[0].qty == 6


def test_market_order_partially_unfilled_when_book_thin():
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 101.0, 3, 0.0, "maker")
    trades, remaining = book.market_order(Side.BUY, 10, 1.0, "taker")
    assert remaining == 7
    assert sum(t.qty for t in trades) == 3
    assert book.best_ask is None


def test_cancel_removes_correct_order_and_level():
    book = LimitOrderBook()
    o1, _ = book.add_limit_order(Side.BUY, 99.0, 5, 0.0, "A")
    o2, _ = book.add_limit_order(Side.BUY, 99.0, 5, 1.0, "B")
    ok = book.cancel(o1.order_id)
    assert ok is True
    level = book.bids[99.0]
    assert len(level) == 1
    assert level[0].agent_id == "B"

    ok2 = book.cancel(o2.order_id)
    assert ok2 is True
    assert 99.0 not in book.bids
    assert book.best_bid is None


def test_cancel_nonexistent_order_returns_false():
    book = LimitOrderBook()
    assert book.cancel(999) is False


def test_book_never_crosses_after_matching_sequence():
    book = LimitOrderBook()
    book.add_limit_order(Side.BUY, 100.0, 5, 0.0, "b1")
    book.add_limit_order(Side.SELL, 101.0, 5, 0.0, "s1")
    book.add_limit_order(Side.BUY, 101.5, 3, 1.0, "b2")  # crosses s1
    book.add_limit_order(Side.SELL, 99.5, 3, 2.0, "s2")  # crosses b1
    bb, ba = book.best_bid, book.best_ask
    if bb is not None and ba is not None:
        assert bb < ba


def test_scripted_sequence_produces_expected_trade_tape():
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 100.0, 5, 0.0, "S1")
    book.add_limit_order(Side.SELL, 100.5, 5, 1.0, "S2")
    book.add_limit_order(Side.BUY, 99.0, 5, 2.0, "B1")

    assert book.best_bid == 99.0
    assert book.best_ask == 100.0
    assert len(book.trade_tape) == 0

    trades, _ = book.market_order(Side.BUY, 8, 3.0, "TAKER")
    assert len(trades) == 2
    assert trades[0].price == 100.0
    assert trades[0].qty == 5
    assert trades[1].price == 100.5
    assert trades[1].qty == 3
    assert len(book.trade_tape) == 2
    assert book.best_ask == 100.5
    assert book.asks[100.5][0].qty == 2
    assert book.best_bid == 99.0


def test_depth_and_imbalance():
    book = LimitOrderBook()
    book.add_limit_order(Side.BUY, 100.0, 10, 0.0, "A")
    book.add_limit_order(Side.SELL, 101.0, 2, 0.0, "B")
    d = book.depth(5)
    assert d["bids"] == [(100.0, 10)]
    assert d["asks"] == [(101.0, 2)]
    imb = book.imbalance(5)
    assert imb == pytest.approx((10 - 2) / 12)


def test_market_order_on_empty_book_is_fully_unfilled():
    book = LimitOrderBook()
    trades, remaining = book.market_order(Side.BUY, 5, 0.0, "taker")
    assert trades == []
    assert remaining == 5


def test_depth_and_imbalance_on_empty_book():
    book = LimitOrderBook()
    d = book.depth(5)
    assert d == {"bids": [], "asks": []}
    assert book.imbalance(5) is None
    assert book.mid_price is None
    assert book.spread is None


def test_cancel_of_already_filled_order_returns_false():
    book = LimitOrderBook()
    o1, _ = book.add_limit_order(Side.BUY, 100.0, 5, 0.0, "maker")
    # fully fills and removes o1 from the book's internal order index
    trades, remaining = book.market_order(Side.SELL, 5, 1.0, "taker")
    assert remaining == 0
    assert trades[0].qty == 5

    assert book.cancel(o1.order_id) is False


def test_limit_order_walks_multiple_levels():
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 100.0, 2, 0.0, "s1")
    book.add_limit_order(Side.SELL, 100.5, 2, 0.0, "s2")
    book.add_limit_order(Side.SELL, 101.0, 2, 0.0, "s3")
    order, trades = book.add_limit_order(Side.BUY, 100.75, 5, 1.0, "aggr")
    assert sum(t.qty for t in trades) == 4
    assert order.qty == 1
    assert book.best_bid == 100.75
    assert book.best_ask == 101.0
