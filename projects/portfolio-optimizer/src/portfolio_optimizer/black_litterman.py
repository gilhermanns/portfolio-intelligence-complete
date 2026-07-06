"""Black-Litterman posterior expected returns.

Steps: (1) reverse-optimize equilibrium returns pi = delta * Sigma @ w_mkt
from market-cap-proxy weights, (2) combine pi with investor views (P, Q, Omega)
via the standard Bayesian mixing formula to get posterior mu and Sigma.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class View:
    """A single investor view.

    ``assets`` maps ticker -> loading. An absolute view on one asset is
    {"AAPL": 1.0}; a relative view ("tech basket outperforms financials
    basket") is {"AAPL": 0.5, "GOOG": 0.5, "JPM": -0.5, "MA": -0.5}.
    ``q`` is the annualized view return, e.g. 0.05 for "outperforms by 5%/yr".
    ``confidence`` in (0, 1] scales the view's uncertainty: 1.0 is very
    confident (tight Omega), values near 0 are nearly ignored.
    """

    assets: dict[str, float]
    q: float
    confidence: float = 0.5


def equilibrium_returns(cov: pd.DataFrame, market_weights: pd.Series, delta: float = 2.5) -> pd.Series:
    w_mkt = market_weights.reindex(cov.columns).fillna(0).values
    pi = delta * cov.values @ w_mkt
    return pd.Series(pi, index=cov.columns)


def _build_view_matrices(views: list[View], tickers: list[str]) -> tuple[np.ndarray, np.ndarray]:
    P = np.zeros((len(views), len(tickers)))
    Q = np.zeros(len(views))
    for i, view in enumerate(views):
        for ticker, loading in view.assets.items():
            P[i, tickers.index(ticker)] = loading
        Q[i] = view.q
    return P, Q


def posterior(
    cov: pd.DataFrame,
    market_weights: pd.Series,
    views: list[View],
    delta: float = 2.5,
    tau: float = 0.05,
) -> tuple[pd.Series, pd.DataFrame]:
    """Return (posterior mu, posterior Sigma) combining the equilibrium prior with views."""
    tickers = list(cov.columns)
    Sigma = cov.values
    pi = equilibrium_returns(cov, market_weights, delta).values

    if not views:
        return pd.Series(pi, index=tickers), cov.copy()

    P, Q = _build_view_matrices(views, tickers)
    confidences = np.array([max(v.confidence, 1e-4) for v in views])
    # Omega diagonal scales with view uncertainty: tighter (smaller) as confidence -> 1.
    view_variances = np.diag(P @ (tau * Sigma) @ P.T)
    omega_diag = view_variances * (1.0 / confidences - 1.0) + 1e-8
    Omega = np.diag(omega_diag)

    tau_sigma_inv = np.linalg.inv(tau * Sigma)
    omega_inv = np.linalg.inv(Omega)

    posterior_cov_inv = tau_sigma_inv + P.T @ omega_inv @ P
    posterior_cov_of_mean = np.linalg.inv(posterior_cov_inv)
    mu_bl = posterior_cov_of_mean @ (tau_sigma_inv @ pi + P.T @ omega_inv @ Q)

    sigma_bl = Sigma + posterior_cov_of_mean
    return (
        pd.Series(mu_bl, index=tickers),
        pd.DataFrame(sigma_bl, index=tickers, columns=tickers),
    )
