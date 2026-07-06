import numpy as np
import pandas as pd
import pytest

from credit_risk_model.data import FEATURE_COLUMNS, apply_macro_shock
from credit_risk_model.expected_loss import (
    EAD_BASE_BY_PURPOSE,
    EAD_INCOME_SCALE,
    LGD_MEAN_BY_PURPOSE,
    assign_lgd_ead,
    expected_loss_point_estimate,
    simulate_portfolio_losses,
)
from credit_risk_model.pipeline import train_all


def test_expected_loss_point_estimate_hand_checked_toy_portfolio():
    pd_array = np.array([0.10, 0.05, 0.20])
    lgd_array = np.array([0.50, 0.40, 0.60])
    ead_array = np.array([10_000, 20_000, 5_000])
    el = expected_loss_point_estimate(pd_array, lgd_array, ead_array)
    expected = np.array([0.10 * 0.50 * 10_000, 0.05 * 0.40 * 20_000, 0.20 * 0.60 * 5_000])
    assert np.allclose(el, expected)
    assert el.tolist() == pytest.approx([500.0, 400.0, 600.0])
    assert el.sum() == pytest.approx(1500.0)


def test_expected_loss_scales_linearly_in_each_factor():
    pd_array = np.array([0.1])
    lgd_array = np.array([0.5])
    ead_array = np.array([1000.0])
    base = expected_loss_point_estimate(pd_array, lgd_array, ead_array)[0]
    doubled_pd = expected_loss_point_estimate(pd_array * 2, lgd_array, ead_array)[0]
    doubled_ead = expected_loss_point_estimate(pd_array, lgd_array, ead_array * 2)[0]
    assert doubled_pd == pytest.approx(base * 2)
    assert doubled_ead == pytest.approx(base * 2)


def test_assign_lgd_ead_respects_documented_means_in_aggregate():
    n = 20_000
    purpose = np.random.default_rng(0).choice(list(LGD_MEAN_BY_PURPOSE.keys()), size=n)
    income = np.full(n, 50_000.0)
    df = pd.DataFrame({"loan_purpose": purpose, "income": income})
    rng = np.random.default_rng(1)
    lgd, ead = assign_lgd_ead(df, rng)

    for purpose_name, mean_lgd in LGD_MEAN_BY_PURPOSE.items():
        mask = purpose == purpose_name
        assert lgd[mask].mean() == pytest.approx(mean_lgd, abs=0.03)
        expected_ead_mean = EAD_BASE_BY_PURPOSE[purpose_name] + EAD_INCOME_SCALE * 50_000.0
        assert ead[mask].mean() == pytest.approx(expected_ead_mean, rel=0.1)


def test_simulate_portfolio_losses_mean_converges_to_point_estimate():
    rng = np.random.default_rng(2)
    n = 5_000
    purpose = rng.choice(list(LGD_MEAN_BY_PURPOSE.keys()), size=n)
    income = rng.uniform(30_000, 80_000, size=n)
    df = pd.DataFrame({"loan_purpose": purpose, "income": income})
    pd_array = np.full(n, 0.10)

    lgd, ead = assign_lgd_ead(df, np.random.default_rng(3))
    point_estimate_total = expected_loss_point_estimate(pd_array, lgd, ead).sum()

    losses = simulate_portfolio_losses(pd_array, purpose, income, n_sims=1500, rng=rng)
    # Monte Carlo mean should land within ~10% of the analytic point estimate
    assert losses.mean() == pytest.approx(point_estimate_total, rel=0.15)


def test_simulate_portfolio_losses_is_nonnegative_and_varies():
    rng = np.random.default_rng(4)
    n = 500
    purpose = rng.choice(list(LGD_MEAN_BY_PURPOSE.keys()), size=n)
    income = rng.uniform(30_000, 80_000, size=n)
    pd_array = np.full(n, 0.15)
    losses = simulate_portfolio_losses(pd_array, purpose, income, n_sims=500, rng=rng)
    assert (losses >= 0).all()
    assert losses.std() > 0


def test_higher_pd_gives_higher_expected_portfolio_loss():
    rng = np.random.default_rng(5)
    n = 2_000
    purpose = rng.choice(list(LGD_MEAN_BY_PURPOSE.keys()), size=n)
    income = rng.uniform(30_000, 80_000, size=n)
    low_pd = np.full(n, 0.05)
    high_pd = np.full(n, 0.25)
    low_losses = simulate_portfolio_losses(low_pd, purpose, income, n_sims=800, rng=np.random.default_rng(6))
    high_losses = simulate_portfolio_losses(high_pd, purpose, income, n_sims=800, rng=np.random.default_rng(7))
    assert high_losses.mean() > low_losses.mean()


def test_macro_stress_scenario_raises_model_pd_and_portfolio_expected_loss():
    """End-to-end stress test: shifting the macro unemployment_rate feature up
    via apply_macro_shock must raise the *trained model's* re-scored PDs (not
    just the DGP's ground truth), and that PD increase must flow through to a
    higher Monte Carlo expected loss -- otherwise the "stress scenario" in the
    report would be measuring nothing.
    """
    artifacts = train_all(n=8_000, seed=40)
    df = artifacts.df
    calibrator = artifacts.calibrator_isotonic

    pd_base = calibrator.predict_proba(df[FEATURE_COLUMNS])[:, 1]
    shocked_df = apply_macro_shock(df, unemployment_delta=4.0)
    pd_shocked = calibrator.predict_proba(shocked_df[FEATURE_COLUMNS])[:, 1]

    # The shock must not lower any borrower's PD, and must raise it on average.
    assert (pd_shocked >= pd_base - 1e-12).all()
    assert pd_shocked.mean() > pd_base.mean()

    rng = np.random.default_rng(41)
    purpose = df["loan_purpose"].to_numpy()
    income = df["income"].to_numpy()
    base_losses = simulate_portfolio_losses(pd_base, purpose, income, n_sims=500, rng=rng)
    stress_losses = simulate_portfolio_losses(pd_shocked, purpose, income, n_sims=500, rng=rng)
    assert stress_losses.mean() > base_losses.mean()
