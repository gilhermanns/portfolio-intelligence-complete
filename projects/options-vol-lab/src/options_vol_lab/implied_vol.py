"""Implied volatility via Brent's method inverting Black-Scholes."""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from options_vol_lab.pricers.black_scholes import black_scholes_price


def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    rate: float,
    ttm: float,
    option_type: str = "call",
    div: float = 0.0,
    vol_lo: float = 1e-4,
    vol_hi: float = 5.0,
) -> float:
    """Solve for sigma such that BS(sigma) == market_price using Brent's method.

    Raises ValueError if market_price is outside the no-arbitrage bounds
    reachable within [vol_lo, vol_hi], or if the price is below intrinsic
    value.
    """
    intrinsic = (
        max(spot * np.exp(-div * ttm) - strike * np.exp(-rate * ttm), 0.0)
        if option_type == "call"
        else max(strike * np.exp(-rate * ttm) - spot * np.exp(-div * ttm), 0.0)
    )
    if market_price < intrinsic - 1e-10:
        raise ValueError("market_price below intrinsic value; no valid implied vol")

    def objective(vol: float) -> float:
        return black_scholes_price(spot, strike, rate, vol, ttm, option_type, div) - market_price

    f_lo, f_hi = objective(vol_lo), objective(vol_hi)
    if f_lo * f_hi > 0:
        raise ValueError(
            "market_price not bracketed by [vol_lo, vol_hi]; widen bounds"
        )

    return float(brentq(objective, vol_lo, vol_hi, xtol=1e-10, rtol=1e-12, maxiter=200))
