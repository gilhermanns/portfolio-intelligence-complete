"""Portfolio expected-loss simulation: PD x LGD x EAD, with Monte Carlo over the borrower pool.

LGD and EAD are not observed in the synthetic dataset (no recovery or loan-amount
history exists to fit them from), so both are assigned from documented assumed
distributions, conditioned on loan purpose as a stand-in for
secured-vs-unsecured collateral and typical ticket size. These are illustrative
credit-risk assumptions, not calibrated to any real portfolio.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Mean LGD (loss given default, fraction of exposure) by purpose: lower for
# purposes more likely to be secured or backed by a tangible asset.
LGD_MEAN_BY_PURPOSE = {
    "home_improvement": 0.35,
    "major_purchase": 0.40,
    "credit_card": 0.55,
    "debt_consolidation": 0.55,
    "other": 0.55,
    "small_business": 0.65,
}
LGD_CONCENTRATION = 8.0  # Beta(mean*conc, (1-mean)*conc); higher = tighter around the mean

# Base loan size (EAD proxy, in dollars) by purpose, scaled up with income.
EAD_BASE_BY_PURPOSE = {
    "credit_card": 6_000,
    "debt_consolidation": 14_000,
    "home_improvement": 18_000,
    "major_purchase": 22_000,
    "other": 10_000,
    "small_business": 35_000,
}
EAD_INCOME_SCALE = 0.15  # extra exposure as a fraction of annual income
EAD_LOGNORMAL_SIGMA = 0.35  # dispersion of EAD draws around the assumed mean


def assign_lgd_ead(df: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Draw a single realized LGD and EAD per borrower (point estimates for the base portfolio table)."""
    purpose = df["loan_purpose"].to_numpy()
    lgd_mean = np.array([LGD_MEAN_BY_PURPOSE[p] for p in purpose])
    alpha = lgd_mean * LGD_CONCENTRATION
    beta = (1 - lgd_mean) * LGD_CONCENTRATION
    lgd = rng.beta(alpha, beta)

    ead_mean = np.array([EAD_BASE_BY_PURPOSE[p] for p in purpose]) + EAD_INCOME_SCALE * df["income"].to_numpy()
    mu = np.log(ead_mean) - 0.5 * EAD_LOGNORMAL_SIGMA**2  # so that E[EAD] == ead_mean
    ead = rng.lognormal(mu, EAD_LOGNORMAL_SIGMA)
    return lgd, ead


def expected_loss_point_estimate(pd_array: np.ndarray, lgd_array: np.ndarray, ead_array: np.ndarray) -> np.ndarray:
    """Per-borrower expected loss EL_i = PD_i * LGD_i * EAD_i (no randomness, closed form)."""
    return np.asarray(pd_array) * np.asarray(lgd_array) * np.asarray(ead_array)


def simulate_portfolio_losses(
    pd_array: np.ndarray,
    purpose: np.ndarray,
    income: np.ndarray,
    n_sims: int,
    rng: np.random.Generator,
    chunk_size: int = 250,
) -> np.ndarray:
    """Monte Carlo distribution of total portfolio loss, resampling default, LGD, and EAD each draw.

    Each simulated year: a Bernoulli default draw per borrower using their PD,
    an independent LGD draw per defaulted borrower, and an independent EAD draw
    per defaulted borrower. Losses are summed across the portfolio for each of
    ``n_sims`` simulated years, returned as an array of length ``n_sims``.
    """
    n = len(pd_array)
    pd_array = np.asarray(pd_array)
    lgd_mean = np.array([LGD_MEAN_BY_PURPOSE[p] for p in purpose])
    alpha = lgd_mean * LGD_CONCENTRATION
    beta = (1 - lgd_mean) * LGD_CONCENTRATION
    ead_mean = np.array([EAD_BASE_BY_PURPOSE[p] for p in purpose]) + EAD_INCOME_SCALE * np.asarray(income)
    mu = np.log(ead_mean) - 0.5 * EAD_LOGNORMAL_SIGMA**2

    losses = np.empty(n_sims)
    done = 0
    while done < n_sims:
        m = min(chunk_size, n_sims - done)
        defaults = rng.random((m, n)) < pd_array[None, :]
        lgd_draws = rng.beta(alpha[None, :] * np.ones((m, 1)), beta[None, :] * np.ones((m, 1)))
        ead_draws = rng.lognormal(mu[None, :] * np.ones((m, 1)), EAD_LOGNORMAL_SIGMA)
        chunk_losses = (defaults * lgd_draws * ead_draws).sum(axis=1)
        losses[done : done + m] = chunk_losses
        done += m
    return losses
