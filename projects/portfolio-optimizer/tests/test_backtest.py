import numpy as np

from portfolio_optimizer.backtest import _rebalance_dates


def test_rebalance_dates_cover_nearly_every_calendar_month(prices, tickers):
    """Regression guard: _rebalance_dates used to intersect calendar
    month-end (from `resample("ME")`) against the trading calendar and fall
    back to the correct per-month last-trading-day list only `if` that
    intersection came back empty. Calendar month-end is a weekend or holiday
    far more often than not, so the intersection was usually a nonempty but
    incomplete list (roughly 2 months in 3 in this panel) and the `or`
    fallback silently never ran, quietly dropping about a third of months
    from the rebalance schedule instead of raising anything. Every calendar
    month actually present in the panel should produce exactly one
    rebalance date, and that date should be a real trading day.
    """
    panel = prices[tickers]
    all_dates = _rebalance_dates(panel, window_months=0)
    n_calendar_months = panel.index.to_period("M").nunique()
    assert len(all_dates) == n_calendar_months
    assert all(d in panel.index for d in all_dates)


def test_backtest_produces_a_value_series_per_strategy(backtest_result):
    expected = {"EqualWeight", "MinVariance", "MaxSharpe", "RiskParity", "BlackLitterman", "SPY"}
    assert expected.issubset(set(backtest_result.values.columns))
    assert backtest_result.values.index.is_monotonic_increasing
    assert not backtest_result.values.isna().any().any()


def test_backtest_values_start_near_one_and_stay_positive(backtest_result):
    for col in backtest_result.values.columns:
        series = backtest_result.values[col]
        assert series.iloc[0] == pytest_approx_one(series.iloc[0])
        assert (series > 0).all()


def pytest_approx_one(x):
    assert abs(x - 1.0) < 1e-6
    return x


def test_turnover_is_bounded_between_zero_and_two(backtest_result):
    turnover = backtest_result.turnover.drop(columns=["EqualWeight"], errors="ignore")
    assert (turnover.dropna() >= 0).all().all()
    assert (turnover.dropna() <= 2.0001).all().all()


def test_metrics_dataframe_has_expected_columns_and_finite_values(backtest_result):
    metrics = backtest_result.metrics()
    for col in ("CAGR", "AnnVol", "Sharpe", "MaxDrawdown", "TrackingErrorVsSPY"):
        assert col in metrics.columns
        assert np.isfinite(metrics[col]).all()
    assert (metrics["MaxDrawdown"] <= 0).all()
    assert (metrics["AnnVol"] > 0).all()


def test_spy_benchmark_has_zero_tracking_error_against_itself(backtest_result):
    metrics = backtest_result.metrics()
    assert metrics.loc["SPY", "TrackingErrorVsSPY"] == 0.0


def test_min_variance_realized_vol_is_lowest_or_near_lowest(backtest_result):
    metrics = backtest_result.metrics()
    strategy_vols = metrics.drop(index="SPY")["AnnVol"]
    # min-variance should rank at or near the bottom of realized vol among optimized strategies
    assert strategy_vols["MinVariance"] <= strategy_vols.median()
