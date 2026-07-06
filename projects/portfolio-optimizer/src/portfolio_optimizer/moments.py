"""Return and covariance estimation from a price panel."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna(how="all")


def monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    monthly_prices = prices.resample("ME").last()
    return monthly_prices.pct_change().dropna(how="all")


def annualized_mean_cov(returns: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    mu = returns.mean() * TRADING_DAYS
    cov = returns.cov() * TRADING_DAYS
    return mu, cov


def shrink_covariance(cov: pd.DataFrame, shrinkage: float = 0.1) -> pd.DataFrame:
    """Ledoit-Wolf-style shrinkage toward a scaled identity (constant-variance) target."""
    if not (0.0 <= shrinkage <= 1.0):
        raise ValueError("shrinkage must be in [0, 1]")
    avg_var = np.trace(cov.values) / cov.shape[0]
    target = np.eye(cov.shape[0]) * avg_var
    shrunk = (1 - shrinkage) * cov.values + shrinkage * target
    return pd.DataFrame(shrunk, index=cov.index, columns=cov.columns)
