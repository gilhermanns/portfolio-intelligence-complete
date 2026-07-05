"""Synthetic borrower-level data generating process (DGP) for credit default risk.

This module fabricates a labeled dataset because no real labeled credit dataset
(Lending Club, UCI German Credit, etc.) is reachable in this environment without
manual account-gated downloads. The DGP below is documented in full so results
are reproducible and so the true, generating relationship between features and
default risk is knowable (useful for sanity-checking the fitted models).

To use a real dataset instead: build a CSV with the columns listed in
``FEATURE_COLUMNS`` plus a binary ``default`` column, and load it with
``pandas.read_csv`` in place of ``generate_borrowers``. Continuous features
should be on comparable raw scales (income in dollars, ratios in [0, 1],
years, counts) since the pipeline's ``ColumnTransformer`` scales them itself.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "income",
    "dti",
    "utilization",
    "credit_history_years",
    "delinquencies_2y",
    "unemployment_rate",
]
CATEGORICAL_FEATURES = ["loan_purpose", "employment_status"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "default"

LOAN_PURPOSES = [
    "debt_consolidation",
    "credit_card",
    "home_improvement",
    "major_purchase",
    "small_business",
    "other",
]
EMPLOYMENT_STATUSES = ["employed", "self_employed", "unemployed", "retired"]

# Purpose and employment risk offsets on the logit scale: the DGP's ground truth
# for how much each segment shifts default risk relative to the baseline.
_PURPOSE_LOGIT_OFFSET = {
    "debt_consolidation": 0.15,
    "credit_card": 0.05,
    "home_improvement": -0.35,
    "major_purchase": -0.10,
    "small_business": 0.55,
    "other": 0.10,
}
_EMPLOYMENT_LOGIT_OFFSET = {
    "employed": -0.20,
    "self_employed": 0.10,
    "unemployed": 1.35,
    "retired": -0.30,
}

# Population moments used to standardize raw features inside the DGP. These are
# fixed constants of the generating process, not estimated from a sample, so
# using them to build the true PD introduces no label leakage into the model.
_LOG_INCOME_MEAN, _LOG_INCOME_STD = np.log(55_000), 0.55
_DTI_ALPHA, _DTI_BETA = 2.2, 5.0  # Beta(2.2, 5.0), mean ~0.31
_UTIL_ALPHA, _UTIL_BETA = 2.0, 2.5  # Beta(2.0, 2.5), mean ~0.44
_HISTORY_SHAPE, _HISTORY_SCALE = 2.0, 5.5  # Gamma, mean 11 years
_DELINQ_LAMBDA = 0.35  # Poisson mean delinquencies in last 2 years
_UNEMP_MEAN, _UNEMP_STD = 5.0, 1.4  # percent, truncated to [2.5, 12]

_DTI_Z_MEAN, _DTI_Z_STD = _DTI_ALPHA / (_DTI_ALPHA + _DTI_BETA), 0.14
_UTIL_Z_MEAN, _UTIL_Z_STD = _UTIL_ALPHA / (_UTIL_ALPHA + _UTIL_BETA), 0.20
_HISTORY_Z_MEAN, _HISTORY_Z_STD = _HISTORY_SHAPE * _HISTORY_SCALE, 7.8
_UNEMP_Z_MEAN, _UNEMP_Z_STD = _UNEMP_MEAN, _UNEMP_STD


def _true_logit(df: pd.DataFrame) -> np.ndarray:
    """Ground-truth (nonlinear) logit of default probability given features."""
    z_income = (np.log(df["income"]) - _LOG_INCOME_MEAN) / _LOG_INCOME_STD
    z_dti = (df["dti"] - _DTI_Z_MEAN) / _DTI_Z_STD
    z_util = (df["utilization"] - _UTIL_Z_MEAN) / _UTIL_Z_STD
    z_hist = (df["credit_history_years"] - _HISTORY_Z_MEAN) / _HISTORY_Z_STD
    z_unemp = (df["unemployment_rate"] - _UNEMP_Z_MEAN) / _UNEMP_Z_STD
    delinq = df["delinquencies_2y"].to_numpy(dtype=float)

    purpose_offset = df["loan_purpose"].map(_PURPOSE_LOGIT_OFFSET).to_numpy()
    employment_offset = df["employment_status"].map(_EMPLOYMENT_LOGIT_OFFSET).to_numpy()
    is_unemployed = (df["employment_status"] == "unemployed").to_numpy(dtype=float)

    logit = (
        0.95 * z_dti
        + 0.75 * z_util
        - 0.85 * z_income
        - 0.55 * z_hist
        + 0.40 * np.minimum(delinq, 6.0)
        + 0.50 * z_unemp
        + 0.30 * z_dti**2  # heavy DTI borrowers deteriorate faster than linearly
        + 0.35 * z_dti * z_util  # high DTI compounds with high utilization
        + 0.45 * is_unemployed * z_unemp  # macro shocks bite unemployed borrowers hardest
        + purpose_offset
        + employment_offset
    )
    return logit


def _calibrate_intercept(df: pd.DataFrame, target_rate: float, noise_std: float, rng: np.random.Generator) -> float:
    """Bisection search for the intercept that hits ``target_rate`` in expectation."""
    base_logit = _true_logit(df)
    noise = rng.normal(0.0, noise_std, size=len(df))

    lo, hi = -10.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        p = 1.0 / (1.0 + np.exp(-(base_logit + noise + mid)))
        if p.mean() > target_rate:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def generate_borrowers(
    n: int = 20_000,
    seed: int = 42,
    target_default_rate: float = 0.10,
    noise_std: float = 2.5,
) -> pd.DataFrame:
    """Generate a synthetic borrower-level dataset with a nonlinear default DGP.

    Parameters
    ----------
    n: number of borrowers to simulate.
    seed: seed for full reproducibility.
    target_default_rate: expected fraction of defaults, hit via intercept calibration.
    noise_std: standard deviation of unobserved-heterogeneity noise added to the
        true logit before drawing labels; this is what caps the achievable AUC
        of any model, since real risk factors are never fully observed.
    """
    rng = np.random.default_rng(seed)

    income = rng.lognormal(mean=_LOG_INCOME_MEAN, sigma=_LOG_INCOME_STD, size=n)
    dti = rng.beta(_DTI_ALPHA, _DTI_BETA, size=n)
    utilization = rng.beta(_UTIL_ALPHA, _UTIL_BETA, size=n)
    credit_history_years = rng.gamma(_HISTORY_SHAPE, _HISTORY_SCALE, size=n)
    delinquencies_2y = rng.poisson(_DELINQ_LAMBDA, size=n).astype(float)
    unemployment_rate = np.clip(rng.normal(_UNEMP_MEAN, _UNEMP_STD, size=n), 2.5, 12.0)
    loan_purpose = rng.choice(LOAN_PURPOSES, size=n, p=[0.30, 0.22, 0.14, 0.12, 0.10, 0.12])
    employment_status = rng.choice(EMPLOYMENT_STATUSES, size=n, p=[0.68, 0.14, 0.08, 0.10])

    df = pd.DataFrame(
        {
            "income": income,
            "dti": dti,
            "utilization": utilization,
            "credit_history_years": credit_history_years,
            "delinquencies_2y": delinquencies_2y,
            "unemployment_rate": unemployment_rate,
            "loan_purpose": loan_purpose,
            "employment_status": employment_status,
        }
    )

    intercept = _calibrate_intercept(df, target_default_rate, noise_std, rng)
    noise = rng.normal(0.0, noise_std, size=n)
    logit = _true_logit(df) + noise + intercept
    true_pd = 1.0 / (1.0 + np.exp(-logit))
    default = rng.binomial(1, true_pd)

    df["true_pd"] = true_pd
    df[TARGET_COLUMN] = default
    df.insert(0, "borrower_id", np.arange(1, n + 1))
    return df


def apply_macro_shock(df: pd.DataFrame, unemployment_delta: float) -> pd.DataFrame:
    """Return a copy of ``df`` with the macro unemployment feature shifted, for stress testing."""
    shocked = df.copy()
    shocked["unemployment_rate"] = np.clip(shocked["unemployment_rate"] + unemployment_delta, 0.5, 25.0)
    return shocked
