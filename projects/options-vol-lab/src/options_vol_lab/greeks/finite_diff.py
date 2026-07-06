"""Central finite-difference Greeks, computed directly on a pricer callable.

Used to cross-check the closed-form Greeks in ``analytic.py`` against a
pricer-agnostic numerical approximation (works for any pricer, e.g. binomial
or Monte Carlo, not just Black-Scholes).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def finite_difference_greeks(
    pricer: Callable[..., float],
    spot: float,
    strike: float,
    rate: float,
    vol: float,
    ttm: float,
    option_type: str = "call",
    div: float = 0.0,
    h_spot: float = 1e-2,
    h_vol: float = 1e-4,
    h_ttm: float = 1e-4,
    h_rate: float = 1e-4,
    **pricer_kwargs,
) -> Greeks:
    """Central differences. ``pricer`` must accept (spot, strike, rate, vol,
    ttm, option_type, div, **pricer_kwargs) and return a scalar price."""

    def price(s=spot, k=strike, r=rate, v=vol, t=ttm):
        return pricer(s, k, r, v, t, option_type, div, **pricer_kwargs)

    p0 = price()

    delta = (price(s=spot + h_spot) - price(s=spot - h_spot)) / (2 * h_spot)
    gamma = (
        price(s=spot + h_spot) - 2 * p0 + price(s=spot - h_spot)
    ) / (h_spot**2)
    vega = (price(v=vol + h_vol) - price(v=vol - h_vol)) / (2 * h_vol)
    # theta: decrease in ttm as time passes -> negative of d(price)/d(ttm)
    theta = -(price(t=ttm + h_ttm) - price(t=ttm - h_ttm)) / (2 * h_ttm)
    rho = (price(r=rate + h_rate) - price(r=rate - h_rate)) / (2 * h_rate)

    return Greeks(delta=float(delta), gamma=float(gamma), vega=float(vega),
                   theta=float(theta), rho=float(rho))
