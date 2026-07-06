"""Cox-Ross-Rubinstein binomial tree pricer, European and American exercise."""
from __future__ import annotations

import numpy as np


def binomial_price(
    spot: float,
    strike: float,
    rate: float,
    vol: float,
    ttm: float,
    option_type: str = "call",
    div: float = 0.0,
    steps: int = 200,
    american: bool = False,
) -> float:
    """CRR binomial tree price.

    American exercise is checked at every node by comparing continuation value
    against immediate exercise value; European collapses to discounted
    expectation only (no early-exercise check).
    """
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if ttm <= 0 or vol <= 0:
        raise ValueError("time to maturity and volatility must be positive")
    dt = ttm / steps
    u = np.exp(vol * np.sqrt(dt))
    d = 1.0 / u
    disc = np.exp(-rate * dt)
    p = (np.exp((rate - div) * dt) - d) / (u - d)
    if not (0.0 < p < 1.0):
        raise ValueError(
            "risk-neutral probability out of (0, 1); reduce steps or check inputs"
        )

    j = np.arange(steps + 1)
    terminal_spot = spot * (u ** (steps - j)) * (d**j)
    if option_type == "call":
        values = np.maximum(terminal_spot - strike, 0.0)
    elif option_type == "put":
        values = np.maximum(strike - terminal_spot, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    for step in range(steps - 1, -1, -1):
        values = disc * (p * values[:-1] + (1 - p) * values[1:])
        if american:
            j = np.arange(step + 1)
            spot_at_step = spot * (u ** (step - j)) * (d**j)
            if option_type == "call":
                exercise = np.maximum(spot_at_step - strike, 0.0)
            else:
                exercise = np.maximum(strike - spot_at_step, 0.0)
            values = np.maximum(values, exercise)

    return float(values[0])
