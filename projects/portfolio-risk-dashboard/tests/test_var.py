import numpy as np
import pandas as pd
import pytest
from scipy import stats

from risk_dashboard import var


@pytest.fixture(scope="module")
def gaussian_returns():
    rng = np.random.default_rng(7)
    mu, sigma = 0.0004, 0.012
    return pd.Series(rng.normal(mu, sigma, 250_000))


def test_parametric_var_normal_matches_closed_form():
    # Closed-form check against the *sample* mean/std the function itself estimates
    # (not the true generating parameters, which a finite sample won't hit exactly).
    rng = np.random.default_rng(1)
    returns = rng.normal(0.001, 0.02, 1_000_000)
    mu, sigma = returns.mean(), returns.std(ddof=1)

    for alpha in (0.95, 0.99):
        expected = -(mu + sigma * stats.norm.ppf(1 - alpha))
        got = var.parametric_var_normal(returns, alpha)
        assert got == pytest.approx(expected, rel=1e-6)


def test_parametric_es_normal_matches_closed_form():
    rng = np.random.default_rng(2)
    returns = rng.normal(0.001, 0.02, 1_000_000)
    mu, sigma = returns.mean(), returns.std(ddof=1)

    for alpha in (0.95, 0.99):
        q = 1 - alpha
        z = stats.norm.ppf(q)
        expected = -(mu - sigma * stats.norm.pdf(z) / q)
        got = var.parametric_es_normal(returns, alpha)
        assert got == pytest.approx(expected, rel=1e-6)


def test_parametric_normal_recovers_theoretical_var_on_synthetic_data(gaussian_returns):
    mu, sigma = 0.0004, 0.012
    theoretical_var_95 = -(mu + sigma * stats.norm.ppf(0.05))
    theoretical_var_99 = -(mu + sigma * stats.norm.ppf(0.01))

    assert var.parametric_var_normal(gaussian_returns, 0.95) == pytest.approx(theoretical_var_95, rel=0.03)
    assert var.parametric_var_normal(gaussian_returns, 0.99) == pytest.approx(theoretical_var_99, rel=0.03)


def test_historical_var_is_correct_empirical_quantile():
    rng = np.random.default_rng(3)
    returns = rng.normal(0.0, 0.01, 5000)

    for alpha in (0.90, 0.95, 0.99):
        expected = -np.quantile(returns, 1 - alpha)
        assert var.historical_var(returns, alpha) == pytest.approx(expected)


def test_historical_var_on_known_discrete_series():
    # 100 evenly spaced returns from -0.99 to 0.00 (step 0.01); the 5th percentile
    # (alpha=0.95) of this exact uniform grid is analytically the 5th-smallest value.
    returns = np.linspace(-0.99, 0.0, 100)
    q = np.quantile(returns, 0.05)
    assert var.historical_var(returns, 0.95) == pytest.approx(-q)


def test_historical_es_is_worse_than_historical_var():
    rng = np.random.default_rng(4)
    returns = rng.standard_t(df=3, size=20000) * 0.01  # fat-tailed
    v = var.historical_var(returns, 0.95)
    es = var.historical_es(returns, 0.95)
    assert es > v  # ES averages the tail beyond VaR, so must be at least as severe


def test_historical_beats_parametric_normal_on_fat_tailed_data():
    # Student-t synthetic returns have fatter tails than Normal; historical ES should
    # exceed the Normal-parametric ES estimated from the same sample, at 99%.
    rng = np.random.default_rng(5)
    returns = rng.standard_t(df=3, size=50000) * 0.01
    hist_es_99 = var.historical_es(returns, 0.99)
    param_es_99 = var.parametric_es_normal(returns, 0.99)
    assert hist_es_99 > param_es_99


def test_monte_carlo_converges_near_parametric_on_gaussian_synthetic_data():
    rng = np.random.default_rng(6)
    n = 4000
    mu = np.array([0.0003, 0.0002])
    cov = np.array([[0.012**2, 0.6 * 0.012 * 0.01], [0.6 * 0.012 * 0.01, 0.01**2]])
    L = np.linalg.cholesky(cov)
    shocks = rng.standard_normal((n, 2)) @ L.T + mu
    returns_df = pd.DataFrame(shocks, columns=["A", "B"])
    weights = {"A": 0.6, "B": 0.4}

    port_returns = returns_df["A"] * 0.6 + returns_df["B"] * 0.4
    mc_var, mc_es, _ = var.monte_carlo_var_es(returns_df, weights, alpha=0.95, n_sims=200_000, seed=99)
    param_var = var.parametric_var_normal(port_returns, 0.95)
    param_es = var.parametric_es_normal(port_returns, 0.95)

    assert mc_var == pytest.approx(param_var, rel=0.08)
    assert mc_es == pytest.approx(param_es, rel=0.08)


def test_var_es_table_confidence_ordering():
    rng = np.random.default_rng(8)
    returns = pd.Series(rng.normal(0.0002, 0.015, 3000))
    table = var.var_es_table(returns, alpha_levels=(0.95, 0.99))
    # Higher confidence must imply a larger (more conservative) VaR and ES.
    assert table.loc[0.99, "historical_VaR"] > table.loc[0.95, "historical_VaR"]
    assert table.loc[0.99, "historical_ES"] > table.loc[0.99, "historical_VaR"]
    assert table.loc[0.95, "historical_ES"] > table.loc[0.95, "historical_VaR"]
