import numpy as np
import pytest

from portfolio_optimizer.black_litterman import View, equilibrium_returns, posterior


def test_no_views_returns_exact_equilibrium_prior(cov, market_weights):
    mu_bl, cov_bl = posterior(cov, market_weights, views=[])
    pi = equilibrium_returns(cov, market_weights)
    assert np.allclose(mu_bl.values, pi.values)
    assert np.allclose(cov_bl.values, cov.values)


def test_strong_absolute_view_pulls_posterior_toward_the_view(cov, market_weights):
    pi = equilibrium_returns(cov, market_weights)
    strong_view = [View(assets={"AAPL": 1.0}, q=0.40, confidence=0.99)]
    mu_bl, _ = posterior(cov, market_weights, views=strong_view)
    # posterior must move from the prior toward the (much higher) view return...
    assert mu_bl["AAPL"] > pi["AAPL"]
    # ...and land close to the view since confidence is near 1
    assert abs(mu_bl["AAPL"] - 0.40) < abs(pi["AAPL"] - 0.40)


def test_higher_confidence_shifts_posterior_further(cov, market_weights):
    pi = equilibrium_returns(cov, market_weights)
    low_conf = posterior(cov, market_weights, [View(assets={"AAPL": 1.0}, q=0.40, confidence=0.05)])[0]
    high_conf = posterior(cov, market_weights, [View(assets={"AAPL": 1.0}, q=0.40, confidence=0.95)])[0]
    dist_low = abs(low_conf["AAPL"] - pi["AAPL"])
    dist_high = abs(high_conf["AAPL"] - pi["AAPL"])
    assert dist_high > dist_low


def test_relative_view_moves_both_legs_in_opposite_directions(cov, market_weights):
    pi = equilibrium_returns(cov, market_weights)
    view = [View(assets={"AAPL": 1.0, "JPM": -1.0}, q=0.10, confidence=0.9)]
    mu_bl, _ = posterior(cov, market_weights, views=view)
    aapl_shift = mu_bl["AAPL"] - pi["AAPL"]
    jpm_shift = mu_bl["JPM"] - pi["JPM"]
    assert aapl_shift > 0
    assert jpm_shift < 0


def test_posterior_covariance_is_larger_than_prior(cov, market_weights):
    # BL posterior Sigma = Sigma + uncertainty-of-the-mean term, so variances can only grow
    view = [View(assets={"AAPL": 1.0}, q=0.40, confidence=0.5)]
    _, cov_bl = posterior(cov, market_weights, views=view)
    assert (np.diag(cov_bl.values) >= np.diag(cov.values) - 1e-12).all()


def test_equilibrium_returns_scale_with_delta(cov, market_weights):
    pi_low = equilibrium_returns(cov, market_weights, delta=1.0)
    pi_high = equilibrium_returns(cov, market_weights, delta=5.0)
    assert np.allclose(pi_high.values, 5.0 * pi_low.values)
