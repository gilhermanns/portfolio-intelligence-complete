"""Closed-form Black-Scholes Greeks."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

from options_vol_lab.pricers.black_scholes import _d1_d2


@dataclass
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def analytic_greeks(
    spot: float,
    strike: float,
    rate: float,
    vol: float,
    ttm: float,
    option_type: str = "call",
    div: float = 0.0,
) -> Greeks:
    d1, d2 = _d1_d2(spot, strike, rate, vol, ttm, div)
    disc_q = np.exp(-div * ttm)
    disc_r = np.exp(-rate * ttm)
    pdf_d1 = norm.pdf(d1)

    gamma = disc_q * pdf_d1 / (spot * vol * np.sqrt(ttm))
    vega = spot * disc_q * pdf_d1 * np.sqrt(ttm)

    if option_type == "call":
        delta = disc_q * norm.cdf(d1)
        theta = (
            -spot * disc_q * pdf_d1 * vol / (2 * np.sqrt(ttm))
            - rate * strike * disc_r * norm.cdf(d2)
            + div * spot * disc_q * norm.cdf(d1)
        )
        rho = strike * ttm * disc_r * norm.cdf(d2)
    elif option_type == "put":
        delta = disc_q * (norm.cdf(d1) - 1.0)
        theta = (
            -spot * disc_q * pdf_d1 * vol / (2 * np.sqrt(ttm))
            + rate * strike * disc_r * norm.cdf(-d2)
            - div * spot * disc_q * norm.cdf(-d1)
        )
        rho = -strike * ttm * disc_r * norm.cdf(-d2)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return Greeks(delta=float(delta), gamma=float(gamma), vega=float(vega),
                   theta=float(theta), rho=float(rho))
