import pandas as pd
import pytest

from walkforward_backtester.strategies import (
    BuyAndHold,
    DonchianBreakout,
    MovingAverageCrossover,
    RSIMeanReversion,
)


def test_ma_crossover_goes_long_when_fast_crosses_above_slow(crossover_ohlc):
    strat = MovingAverageCrossover(fast=3, slow=6)
    pos = strat.generate_signals(crossover_ohlc)

    assert pos.loc["2020-01-13"] == 0
    assert pos.loc["2020-01-14"] == 1
    assert pos.loc["2020-01-30"] == 1
    assert pos.loc["2020-01-31"] == 0


def test_ma_crossover_flat_during_indicator_warmup(crossover_ohlc):
    strat = MovingAverageCrossover(fast=3, slow=6)
    pos = strat.generate_signals(crossover_ohlc)
    assert (pos.iloc[:5] == 0).all()


def test_ma_crossover_rejects_fast_ge_slow():
    with pytest.raises(ValueError):
        MovingAverageCrossover(fast=50, slow=20)


def test_ma_crossover_allow_short_goes_negative(crossover_ohlc):
    strat = MovingAverageCrossover(fast=3, slow=6, allow_short=True)
    pos = strat.generate_signals(crossover_ohlc)
    assert pos.loc["2020-01-31"] == -1


def test_rsi_enters_on_oversold_and_exits_on_neutral_cross(rsi_ohlc):
    strat = RSIMeanReversion(period=14, oversold=30, overbought=70, exit_neutral=50)
    pos = strat.generate_signals(rsi_ohlc)

    assert pos.loc["2020-01-28"] == 0
    assert pos.loc["2020-01-29"] == 1
    assert pos.loc["2020-02-19"] == 1
    assert pos.loc["2020-02-20"] == 0


def test_rsi_never_enters_before_period_warmup(rsi_ohlc):
    strat = RSIMeanReversion(period=14)
    pos = strat.generate_signals(rsi_ohlc)
    assert (pos.iloc[:14] == 0).all()


def test_rsi_allow_short_enters_on_overbought(rsi_ohlc):
    strat = RSIMeanReversion(period=14, oversold=30, overbought=70, exit_neutral=50, allow_short=True)
    pos = strat.generate_signals(rsi_ohlc)
    assert (pos == -1).any()


def test_donchian_breakout_triggers_on_new_high(breakout_ohlc):
    strat = DonchianBreakout(entry_window=10, exit_window=5)
    pos = strat.generate_signals(breakout_ohlc)

    assert pos.loc["2020-01-28"] == 0
    assert pos.loc["2020-01-29"] == 1
    assert pos.iloc[-1] == 1  # stays long, price never falls back below the trailing low


def test_donchian_rejects_exit_window_larger_than_entry():
    with pytest.raises(ValueError):
        DonchianBreakout(entry_window=5, exit_window=10)


def test_buy_and_hold_is_always_fully_long(crossover_ohlc):
    strat = BuyAndHold()
    pos = strat.generate_signals(crossover_ohlc)
    assert (pos == 1).all()


@pytest.mark.parametrize(
    "strategy_cls", [MovingAverageCrossover, RSIMeanReversion, DonchianBreakout, BuyAndHold]
)
def test_param_grid_nonempty_and_constructible(strategy_cls):
    grid = strategy_cls.param_grid()
    assert len(grid) > 0
    for params in grid:
        strategy_cls(**params)  # should not raise
