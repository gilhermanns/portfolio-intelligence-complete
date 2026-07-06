"""Semi-closed-form Heston (1993) European option pricer.

Uses the Albrecher-Mayer-Schoutens-Tistaert ("Little Heston Trap") formulation
of the characteristic function, which avoids the branch-cut discontinuities
of the original 1993 formula and is stable across long maturities and typical
parameter ranges.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import quad


def _char_func(phi, j, S0, r, q, T, kappa, theta, sigma_v, rho, v0):
    x = np.log(S0)
    if j == 1:
        u = 0.5
        b = kappa - rho * sigma_v
    else:
        u = -0.5
        b = kappa
    a = kappa * theta

    rspi = rho * sigma_v * 1j * phi
    d = np.sqrt((rspi - b) ** 2 - sigma_v**2 * (2 * u * 1j * phi - phi**2))
    c = (b - rspi - d) / (b - rspi + d)

    exp_dT = np.exp(-d * T)
    C = (r - q) * 1j * phi * T + (a / sigma_v**2) * (
        (b - rspi - d) * T - 2 * np.log((1 - c * exp_dT) / (1 - c))
    )
    D = (b - rspi - d) / sigma_v**2 * ((1 - exp_dT) / (1 - c * exp_dT))
    return np.exp(C + D * v0 + 1j * phi * x)


def _prob(j, S0, K, r, q, T, kappa, theta, sigma_v, rho, v0, upper=200.0):
    def integrand(phi):
        cf = _char_func(phi, j, S0, r, q, T, kappa, theta, sigma_v, rho, v0)
        val = np.exp(-1j * phi * np.log(K)) * cf / (1j * phi)
        return val.real

    integral, _ = quad(integrand, 1e-8, upper, limit=200)
    return 0.5 + integral / np.pi


def heston_price(
    spot: float,
    strike: float,
    rate: float,
    ttm: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    v0: float,
    option_type: str = "call",
    div: float = 0.0,
) -> float:
    """Price a European option under Heston (1993) via Fourier inversion.

    Feller condition (2*kappa*theta > sigma_v**2) is not enforced here but
    should hold for the variance process to stay strictly positive in
    continuous time; the pricer remains well defined numerically even when it
    is mildly violated.
    """
    p1 = _prob(1, spot, strike, rate, div, ttm, kappa, theta, sigma_v, rho, v0)
    p2 = _prob(2, spot, strike, rate, div, ttm, kappa, theta, sigma_v, rho, v0)
    call = spot * np.exp(-div * ttm) * p1 - strike * np.exp(-rate * ttm) * p2
    if option_type == "call":
        return float(call)
    elif option_type == "put":
        put = call - spot * np.exp(-div * ttm) + strike * np.exp(-rate * ttm)
        return float(put)
    raise ValueError("option_type must be 'call' or 'put'")
