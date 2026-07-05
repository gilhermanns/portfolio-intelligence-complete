import math

import pytest

from orderbook_sim.metrics import adverse_selection, fill_rates_by_type, realized_volatility
from orderbook_sim.orderbook import Side


class FakeAgent:
    def __init__(self, agent_type, qty_sent, qty_filled):
        self.agent_type = agent_type
        self.qty_sent = qty_sent
        self.qty_filled = qty_filled


def test_realized_volatility_zero_for_constant_price():
    series = [100.0] * 20
    vol = realized_volatility(series, sample_dt=1.0)
    assert vol == pytest.approx(0.0, abs=1e-9)


def test_realized_volatility_positive_for_moving_price():
    series = [100.0, 100.5, 99.8, 100.9, 99.5, 101.0]
    vol = realized_volatility(series, sample_dt=1.0)
    assert vol > 0


def test_realized_volatility_handles_none_values():
    series = [100.0, None, 101.0, None, 100.5, 101.5, 99.0]
    vol = realized_volatility(series, sample_dt=0.5)
    assert vol >= 0
    assert not math.isnan(vol)


def test_fill_rates_by_type_aggregates_correctly():
    agents = {
        "a1": FakeAgent("LP", qty_sent=100.0, qty_filled=80.0),
        "a2": FakeAgent("LP", qty_sent=100.0, qty_filled=60.0),
        "b1": FakeAgent("Noise", qty_sent=50.0, qty_filled=50.0),
    }
    rates = fill_rates_by_type(agents)
    assert rates["LP"] == pytest.approx(140.0 / 200.0)
    assert rates["Noise"] == pytest.approx(1.0)


def test_fill_rates_zero_sent_is_zero_not_error():
    agents = {"a1": FakeAgent("X", qty_sent=0.0, qty_filled=0.0)}
    rates = fill_rates_by_type(agents)
    assert rates["X"] == 0.0


def test_adverse_selection_positive_when_price_moves_against_lp():
    fill_events = [(0.0, Side.BUY, 100.0)]
    mid_history = [(0.0, 100.0), (5.0, 99.0), (10.0, 98.0)]
    cost = adverse_selection(fill_events, mid_history, horizon=5.0)
    assert cost == pytest.approx(100.0 - 99.0)


def test_adverse_selection_for_sell_side_fill():
    fill_events = [(0.0, Side.SELL, 100.0)]
    mid_history = [(0.0, 100.0), (5.0, 101.5)]
    cost = adverse_selection(fill_events, mid_history, horizon=5.0)
    assert cost == pytest.approx(101.5 - 100.0)


def test_adverse_selection_none_when_no_fills():
    assert adverse_selection([], [(0.0, 100.0)], horizon=5.0) is None
