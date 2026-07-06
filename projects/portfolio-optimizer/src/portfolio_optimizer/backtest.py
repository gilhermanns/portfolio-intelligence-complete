"""Rolling monthly re-optimization backtest with transaction costs.

Each strategy is re-optimized at every month-end using a trailing window of
daily returns, then held (no interim trading) until the next rebalance, so
weights drift with relative price moves between rebalances exactly as a real
portfolio would. Transaction costs are charged on realized turnover (target
weights vs. the weights the portfolio had actually drifted to) at every
rebalance, regardless of whether the optimizer itself is turnover-aware.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import black_litterman as bl
from .constraints import Constraints
from .moments import annualized_mean_cov, daily_returns
from .optimizers import OptimizationError, max_sharpe, min_variance, risk_parity
from .universe import market_weights_for

TRADING_DAYS = 252


def _equal_weight(tickers: list[str]) -> pd.Series:
    return pd.Series(1.0 / len(tickers), index=tickers)


def _rebalance_dates(prices: pd.DataFrame, window_months: int) -> list[pd.Timestamp]:
    month_ends = prices.resample("ME").last().index
    month_ends = [d for d in month_ends if d in prices.index] or list(
        prices.groupby(prices.index.to_period("M")).apply(lambda g: g.index[-1])
    )
    if window_months >= len(month_ends):
        raise ValueError("not enough monthly history for the requested trailing window")
    return list(month_ends[window_months:])


def _default_views(tickers: list[str]) -> list[bl.View]:
    views = []
    if "AAPL" in tickers:
        views.append(bl.View(assets={"AAPL": 1.0}, q=0.15, confidence=0.6))
    tech = [t for t in ("AAPL", "GOOG", "META") if t in tickers]
    fin = [t for t in ("JPM", "MA") if t in tickers]
    if tech and fin:
        assets = {t: 1.0 / len(tech) for t in tech} | {t: -1.0 / len(fin) for t in fin}
        views.append(bl.View(assets=assets, q=0.05, confidence=0.4))
    if "GLD" in tickers:
        views.append(bl.View(assets={"GLD": 1.0}, q=0.03, confidence=0.3))
    return views


@dataclass
class BacktestResult:
    values: pd.DataFrame  # date-indexed, one column per strategy (+ SPY benchmark)
    turnover: pd.DataFrame  # rebalance-date-indexed per-strategy turnover
    weights_history: dict[str, pd.DataFrame]  # strategy -> rebalance-date-indexed target weights

    def metrics(self, rf: float = 0.02) -> pd.DataFrame:
        rows = {}
        bench_ret = self.values["SPY"].pct_change().dropna()
        for col in self.values.columns:
            v = self.values[col].dropna()
            ret = v.pct_change().dropna()
            n_years = len(ret) / TRADING_DAYS
            cagr = (v.iloc[-1] / v.iloc[0]) ** (1 / n_years) - 1 if n_years > 0 else np.nan
            vol = ret.std() * np.sqrt(TRADING_DAYS)
            sharpe = (cagr - rf) / vol if vol > 1e-12 else np.nan
            running_max = v.cummax()
            max_dd = ((v - running_max) / running_max).min()
            aligned = pd.concat([ret, bench_ret], axis=1, join="inner")
            tracking_error = (aligned.iloc[:, 0] - aligned.iloc[:, 1]).std() * np.sqrt(TRADING_DAYS)
            avg_turnover = self.turnover[col].mean() if col in self.turnover.columns else np.nan
            rows[col] = {
                "CAGR": cagr,
                "AnnVol": vol,
                "Sharpe": sharpe,
                "MaxDrawdown": max_dd,
                "AvgTurnoverPerRebalance": avg_turnover,
                "TrackingErrorVsSPY": tracking_error,
            }
        return pd.DataFrame(rows).T


def run_backtest(
    prices: pd.DataFrame,
    sector_map: dict[str, str],
    benchmark: pd.Series,
    window_months: int = 30,
    tc_bps: float = 10.0,
    max_weight: float | None = 0.25,
    sector_caps: dict[str, float] | None = None,
    rf: float = 0.02,
) -> BacktestResult:
    tickers = list(prices.columns)
    returns = daily_returns(prices)
    constraints = Constraints(long_only=True, max_weight=max_weight, sector_caps=sector_caps, tc_bps=tc_bps)
    market_weights = pd.Series(market_weights_for(tickers))
    views = _default_views(tickers)

    strategy_names = ["EqualWeight", "MinVariance", "MaxSharpe", "RiskParity", "BlackLitterman"]
    prev_weights: dict[str, pd.Series | None] = {s: None for s in strategy_names}
    port_value: dict[str, float] = {s: 1.0 for s in strategy_names}

    value_rows: list[dict] = []
    turnover_rows: list[dict] = []
    weight_rows: dict[str, list[dict]] = {s: [] for s in strategy_names}

    rebal_dates = _rebalance_dates(prices, window_months)
    window_offset = pd.DateOffset(months=window_months)

    for i, rd in enumerate(rebal_dates[:-1]):
        next_rd = rebal_dates[i + 1]
        window_returns = returns.loc[(rd - window_offset) : rd]
        mu, cov = annualized_mean_cov(window_returns)

        targets: dict[str, pd.Series] = {}
        targets["EqualWeight"] = _equal_weight(tickers)
        try:
            targets["MinVariance"] = min_variance(cov, sector_map, constraints, prev_weights["MinVariance"])
        except OptimizationError:
            targets["MinVariance"] = prev_weights["MinVariance"] or _equal_weight(tickers)
        try:
            targets["MaxSharpe"] = max_sharpe(mu, cov, sector_map, constraints, rf, prev_weights["MaxSharpe"])
        except OptimizationError:
            targets["MaxSharpe"] = prev_weights["MaxSharpe"] or _equal_weight(tickers)
        try:
            targets["RiskParity"] = risk_parity(cov, sector_map, constraints)
        except OptimizationError:
            targets["RiskParity"] = prev_weights["RiskParity"] or _equal_weight(tickers)
        try:
            mu_bl, cov_bl = bl.posterior(cov, market_weights, views)
            targets["BlackLitterman"] = max_sharpe(mu_bl, cov_bl, sector_map, constraints, rf, prev_weights["BlackLitterman"])
        except OptimizationError:
            targets["BlackLitterman"] = prev_weights["BlackLitterman"] or _equal_weight(tickers)

        period_prices = prices.loc[rd:next_rd]
        rel = period_prices / period_prices.iloc[0]

        for name in strategy_names:
            target = targets[name].reindex(tickers).fillna(0)
            drifted = prev_weights[name] if prev_weights[name] is not None else target
            turnover = float((target - drifted.reindex(tickers).fillna(0)).abs().sum())
            cost = (tc_bps / 1e4) * turnover
            port_value[name] *= 1 - cost
            turnover_rows.append({"date": rd, "strategy": name, "turnover": turnover})
            weight_rows[name].append({"date": rd, **target.to_dict()})

            weighted_rel = (rel * target).sum(axis=1)
            day_values = port_value[name] * weighted_rel
            start_idx = 1 if i > 0 else 0  # avoid duplicating the shared boundary date across periods
            for dt, val in day_values.iloc[start_idx:].items():
                value_rows.append({"date": dt, "strategy": name, "value": val})

            port_value[name] = float(day_values.iloc[-1])
            end_drifted = target * rel.iloc[-1]
            prev_weights[name] = end_drifted / end_drifted.sum()

    values = pd.DataFrame(value_rows).pivot(index="date", columns="strategy", values="value")
    bench_window = benchmark.loc[values.index[0] : values.index[-1]]
    values["SPY"] = bench_window / bench_window.iloc[0]

    turnover = pd.DataFrame(turnover_rows).pivot(index="date", columns="strategy", values="turnover")
    weights_history = {name: pd.DataFrame(rows).set_index("date") for name, rows in weight_rows.items()}

    return BacktestResult(values=values, turnover=turnover, weights_history=weights_history)
