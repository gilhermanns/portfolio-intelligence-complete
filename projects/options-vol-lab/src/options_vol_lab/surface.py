"""Build a synthetic implied-vol surface from Monte-Carlo-simulated Heston paths."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from options_vol_lab.heston.simulate import simulate_heston_terminal, mc_price_from_terminal
from options_vol_lab.implied_vol import implied_volatility


@dataclass
class VolSurface:
    strikes: np.ndarray          # absolute strikes
    moneyness: np.ndarray        # K / spot
    maturities: np.ndarray       # in years
    ivs: np.ndarray               # shape (len(maturities), len(strikes))
    spot: float
    rate: float


def build_synthetic_surface(
    spot: float,
    rate: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    v0: float,
    moneyness_grid: np.ndarray,
    maturities: np.ndarray,
    div: float = 0.0,
    n_paths: int = 200_000,
    n_steps_per_year: int = 100,
    seed: int | None = 7,
) -> VolSurface:
    """Simulate Heston terminal-spot distributions (one per maturity) and
    invert Black-Scholes implied vol at each (maturity, strike) node."""
    moneyness_grid = np.asarray(moneyness_grid, dtype=float)
    maturities = np.asarray(maturities, dtype=float)
    strikes = moneyness_grid * spot

    ivs = np.zeros((len(maturities), len(moneyness_grid)))
    rng_seed = seed
    for i, t in enumerate(maturities):
        n_steps = max(int(round(n_steps_per_year * t)), 5)
        terminal = simulate_heston_terminal(
            spot, rate, t, kappa, theta, sigma_v, rho, v0,
            div=div, n_steps=n_steps, n_paths=n_paths,
            seed=None if rng_seed is None else rng_seed + i,
        )
        for k, strike in enumerate(strikes):
            price, _ = mc_price_from_terminal(terminal, strike, rate, t, "call")
            try:
                ivs[i, k] = implied_volatility(price, spot, strike, rate, t, "call", div)
            except ValueError:
                ivs[i, k] = np.nan

    return VolSurface(strikes=strikes, moneyness=moneyness_grid, maturities=maturities,
                       ivs=ivs, spot=spot, rate=rate)
