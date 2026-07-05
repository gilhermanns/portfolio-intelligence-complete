"""Monte Carlo pricer for European options under GBM.

Uses antithetic variates and a control variate (the underlying's own
discounted terminal value, whose expectation is known in closed form under
the risk-neutral measure) to reduce estimator variance.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MCResult:
    price: float
    std_error: float


def monte_carlo_price(
    spot: float,
    strike: float,
    rate: float,
    vol: float,
    ttm: float,
    option_type: str = "call",
    div: float = 0.0,
    n_paths: int = 100_000,
    antithetic: bool = True,
    control_variate: bool = True,
    seed: int | None = None,
) -> MCResult:
    rng = np.random.default_rng(seed)
    n_draws = n_paths // 2 if antithetic else n_paths
    z = rng.standard_normal(n_draws)
    if antithetic:
        z = np.concatenate([z, -z])

    drift = (rate - div - 0.5 * vol**2) * ttm
    diffusion = vol * np.sqrt(ttm) * z
    terminal_spot = spot * np.exp(drift + diffusion)

    if option_type == "call":
        payoff = np.maximum(terminal_spot - strike, 0.0)
    elif option_type == "put":
        payoff = np.maximum(strike - terminal_spot, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    disc = np.exp(-rate * ttm)
    discounted_payoff = disc * payoff

    if control_variate:
        # Control variate: discounted terminal spot, with known mean S*exp(-q*T).
        control = disc * terminal_spot
        control_mean = spot * np.exp(-div * ttm)
        cov = np.cov(discounted_payoff, control)[0, 1]
        var_control = np.var(control)
        beta = cov / var_control if var_control > 0 else 0.0
        adjusted = discounted_payoff - beta * (control - control_mean)
        price = float(np.mean(adjusted))
        std_error = float(np.std(adjusted, ddof=1) / np.sqrt(len(adjusted)))
    else:
        price = float(np.mean(discounted_payoff))
        std_error = float(np.std(discounted_payoff, ddof=1) / np.sqrt(len(discounted_payoff)))

    return MCResult(price=price, std_error=std_error)
