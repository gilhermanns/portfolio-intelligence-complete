"""Black-Scholes closed-form pricing for European options."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _d1_d2(spot: float, strike: float, rate: float, vol: float, ttm: float, div: float = 0.0):
    if ttm <= 0 or vol <= 0:
        raise ValueError("time to maturity and volatility must be positive")
    d1 = (np.log(spot / strike) + (rate - div + 0.5 * vol**2) * ttm) / (vol * np.sqrt(ttm))
    d2 = d1 - vol * np.sqrt(ttm)
    return d1, d2


def black_scholes_price(
    spot: float,
    strike: float,
    rate: float,
    vol: float,
    ttm: float,
    option_type: str = "call",
    div: float = 0.0,
) -> float:
    """Price a European option under Black-Scholes-Merton (constant dividend yield).

    Parameters mirror the standard notation: S (spot), K (strike), r (risk-free
    rate), sigma (annualized vol), T (time to maturity in years), q (continuous
    dividend yield).
    """
    d1, d2 = _d1_d2(spot, strike, rate, vol, ttm, div)
    disc_q = np.exp(-div * ttm)
    disc_r = np.exp(-rate * ttm)
    if option_type == "call":
        return spot * disc_q * norm.cdf(d1) - strike * disc_r * norm.cdf(d2)
    elif option_type == "put":
        return strike * disc_r * norm.cdf(-d2) - spot * disc_q * norm.cdf(-d1)
    raise ValueError("option_type must be 'call' or 'put'")
