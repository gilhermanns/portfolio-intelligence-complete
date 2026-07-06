import numpy as np
import pandas as pd
import pytest

from walkforward_backtester.execution import ExecutionConfig
from walkforward_backtester.strategies import MovingAverageCrossover
from walkforward_backtester.walkforward import WalkForwardSplitter, run_walkforward, stitch_oos_curve


@pytest.fixture
def long_history() -> pd.DataFrame:
    n = 252 * 6  # 6 years of business days
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    rng = np.random.default_rng(7)
    returns = rng.normal(0.0003, 0.01, n)
    prices = 100 * np.cumprod(1 + returns)
    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices * 1.003,
            "Low": prices * 0.997,
            "Close": prices,
            "Volume": 1_000_000,
        },
        index=dates,
    )
    return df


def test_splitter_produces_non_overlapping_chronological_folds(long_history):
    splitter = WalkForwardSplitter(
        train_period=pd.DateOffset(years=2),
        val_period=pd.DateOffset(years=1),
        test_period=pd.DateOffset(months=6),
    )
    folds = splitter.split(long_history.index)
    assert len(folds) > 0

    for fold in folds:
        assert fold.train_start < fold.train_end == fold.val_start
        assert fold.val_start < fold.val_end == fold.test_start
        assert fold.test_start < fold.test_end

    for prev, nxt in zip(folds, folds[1:]):
        # each fold rolls forward in time; the next fold's train never starts
        # before the previous one's, and folds don't skip backward
        assert nxt.train_start >= prev.train_start
        assert nxt.test_start >= prev.test_start


def test_splitter_windows_have_no_lookahead_overlap(long_history):
    splitter = WalkForwardSplitter(
        train_period=pd.DateOffset(years=2),
        val_period=pd.DateOffset(years=1),
        test_period=pd.DateOffset(months=6),
    )
    folds = splitter.split(long_history.index)
    for fold in folds:
        train_dates = long_history.index[(long_history.index >= fold.train_start) & (long_history.index < fold.train_end)]
        val_dates = long_history.index[(long_history.index >= fold.val_start) & (long_history.index < fold.val_end)]
        test_dates = long_history.index[(long_history.index >= fold.test_start) & (long_history.index < fold.test_end)]

        assert set(train_dates).isdisjoint(set(val_dates))
        assert set(val_dates).isdisjoint(set(test_dates))
        assert set(train_dates).isdisjoint(set(test_dates))
        if len(train_dates) and len(val_dates):
            assert train_dates.max() < val_dates.min()
        if len(val_dates) and len(test_dates):
            assert val_dates.max() < test_dates.min()


def test_splitter_respects_custom_step(long_history):
    splitter = WalkForwardSplitter(
        train_period=pd.DateOffset(years=2),
        val_period=pd.DateOffset(years=1),
        test_period=pd.DateOffset(months=6),
        step=pd.DateOffset(months=3),
    )
    folds = splitter.split(long_history.index)
    assert len(folds) > 1
    gap_days = (folds[1].train_start - folds[0].train_start).days
    assert 85 <= gap_days <= 95  # roughly one quarter, per the custom step


def test_splitter_empty_on_insufficient_history():
    short_index = pd.date_range("2024-01-01", periods=50, freq="B")
    splitter = WalkForwardSplitter(
        train_period=pd.DateOffset(years=2),
        val_period=pd.DateOffset(years=1),
        test_period=pd.DateOffset(months=6),
    )
    assert splitter.split(short_index) == []


def test_run_walkforward_test_segment_never_touches_validation_selection(long_history):
    splitter = WalkForwardSplitter(
        train_period=pd.DateOffset(years=2),
        val_period=pd.DateOffset(years=1),
        test_period=pd.DateOffset(months=6),
    )
    config = ExecutionConfig()
    outcomes = run_walkforward(MovingAverageCrossover, long_history, splitter, config)
    assert len(outcomes) > 0
    for outcome in outcomes:
        assert set(outcome.best_params.keys()) == {"fast", "slow"}
        # the selected params must respect the strategy's own constraint
        assert outcome.best_params["fast"] < outcome.best_params["slow"]
        # test result equity curve must be indexed strictly inside the test window
        idx = outcome.test_result.equity_curve.index
        if len(idx):
            assert idx.min() >= outcome.fold.test_start
            assert idx.max() < outcome.fold.test_end


def test_stitched_oos_curve_is_continuous_and_monotonic_index(long_history):
    splitter = WalkForwardSplitter(
        train_period=pd.DateOffset(years=2),
        val_period=pd.DateOffset(years=1),
        test_period=pd.DateOffset(months=6),
    )
    outcomes = run_walkforward(MovingAverageCrossover, long_history, splitter, ExecutionConfig())
    curve = stitch_oos_curve(outcomes, initial_capital=100_000)
    assert curve.index.is_monotonic_increasing
    assert not curve.index.has_duplicates
    assert curve.iloc[0] > 0
