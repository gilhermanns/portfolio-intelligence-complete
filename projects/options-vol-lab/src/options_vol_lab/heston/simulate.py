"""Euler discretization (full-truncation scheme) of the Heston SDE.

    dS_t = (r - q) S_t dt + sqrt(v_t) S_t dW1_t
    dv_t = kappa (theta - v_t) dt + sigma_v sqrt(v_t) dW2_t,  corr(dW1, dW2) = rho

Full truncation (Lord, Koekkoek & van Dijk, 2010) replaces v_t by max(v_t, 0)
wherever it appears, which keeps the discretized variance process well
defined without resorting to reflection or absorption schemes.
"""
from __future__ import annotations

import numpy as np


def simulate_heston_terminal(
    spot: float,
    rate: float,
    ttm: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    v0: float,
    div: float = 0.0,
    n_steps: int = 100,
    n_paths: int = 100_000,
    antithetic: bool = True,
    seed: int | None = None,
) -> np.ndarray:
    """Simulate terminal spot prices S_T under the Heston model.

    Returns an array of shape (n_paths,) of terminal spot values (paths are
    doubled internally when antithetic=True so the returned array still has
    length n_paths, rounded down to an even number in that case).
    """
    rng = np.random.default_rng(seed)
    dt = ttm / n_steps
    sqrt_dt = np.sqrt(dt)

    n_sim = n_paths // 2 if antithetic else n_paths
    log_s = np.full(n_sim, np.log(spot))
    v = np.full(n_sim, v0)
    if antithetic:
        log_s_a = np.full(n_sim, np.log(spot))
        v_a = np.full(n_sim, v0)

    for _ in range(n_steps):
        z1 = rng.standard_normal(n_sim)
        z_indep = rng.standard_normal(n_sim)
        z2 = rho * z1 + np.sqrt(1 - rho**2) * z_indep

        v_pos = np.maximum(v, 0.0)
        log_s += (rate - div - 0.5 * v_pos) * dt + np.sqrt(v_pos) * sqrt_dt * z1
        v = v + kappa * (theta - v_pos) * dt + sigma_v * np.sqrt(v_pos) * sqrt_dt * z2

        if antithetic:
            v_pos_a = np.maximum(v_a, 0.0)
            log_s_a += (rate - div - 0.5 * v_pos_a) * dt + np.sqrt(v_pos_a) * sqrt_dt * (-z1)
            v_a = v_a + kappa * (theta - v_pos_a) * dt + sigma_v * np.sqrt(v_pos_a) * sqrt_dt * (-z2)

    terminal = np.exp(log_s)
    if antithetic:
        terminal = np.concatenate([terminal, np.exp(log_s_a)])
    return terminal


def mc_price_from_terminal(
    terminal_spot: np.ndarray,
    strike: float,
    rate: float,
    ttm: float,
    option_type: str = "call",
) -> tuple[float, float]:
    """Discount and average a terminal-spot sample into an option price.

    Returns (price, standard_error).
    """
    if option_type == "call":
        payoff = np.maximum(terminal_spot - strike, 0.0)
    elif option_type == "put":
        payoff = np.maximum(strike - terminal_spot, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    disc = np.exp(-rate * ttm)
    discounted = disc * payoff
    price = float(np.mean(discounted))
    se = float(np.std(discounted, ddof=1) / np.sqrt(len(discounted)))
    return price, se
