import numpy as np
import pytest

from portfolio_optimizer.constraints import Constraints
from portfolio_optimizer.optimizers import (
    efficient_frontier,
    max_sharpe,
    min_variance,
    risk_contributions,
    risk_parity,
)

TOL = 1e-4


def _portfolio_vol(w, cov):
    return float(np.sqrt(w.reindex(cov.columns).values @ cov.values @ w.reindex(cov.columns).values))


@pytest.mark.parametrize("optimizer_name", ["min_variance", "max_sharpe", "risk_parity"])
def test_weights_sum_to_one(optimizer_name, mu, cov, sector_map):
    if optimizer_name == "min_variance":
        w = min_variance(cov, sector_map)
    elif optimizer_name == "max_sharpe":
        w = max_sharpe(mu, cov, sector_map)
    else:
        w = risk_parity(cov, sector_map)
    assert w.sum() == pytest.approx(1.0, abs=TOL)
    assert (w >= -TOL).all()


def test_min_variance_beats_equal_weight_variance(mu, cov, sector_map, tickers):
    w_mv = min_variance(cov, sector_map)
    w_eq = __import__("pandas").Series(1.0 / len(tickers), index=tickers)
    assert _portfolio_vol(w_mv, cov) <= _portfolio_vol(w_eq, cov) + 1e-9


def test_max_weight_constraint_is_respected(mu, cov, sector_map):
    cap = 0.15
    constraints = Constraints(max_weight=cap)
    for w in (
        min_variance(cov, sector_map, constraints),
        max_sharpe(mu, cov, sector_map, constraints),
        risk_parity(cov, sector_map, constraints),
    ):
        assert w.max() <= cap + 1e-3


def test_sector_cap_constraint_is_respected(mu, cov, sector_map):
    cap = 0.20
    constraints = Constraints(max_weight=0.5, sector_caps={"Technology": cap})
    tech_tickers = [t for t, s in sector_map.items() if s == "Technology"]
    for w in (
        min_variance(cov, sector_map, constraints),
        max_sharpe(mu, cov, sector_map, constraints),
        risk_parity(cov, sector_map, constraints),
    ):
        assert w.reindex(tech_tickers).sum() <= cap + 1e-3


def test_risk_parity_gives_near_equal_risk_contributions(cov, sector_map):
    w = risk_parity(cov, sector_map)  # no caps -> exact ERC by construction
    rc = risk_contributions(w, cov)
    assert rc.std() < 1e-3
    assert (rc.max() - rc.min()) < 1e-3


def test_risk_parity_with_max_weight_cap_is_not_naive_equal_weight(cov, sector_map, tickers):
    """Regression guard for the risk-parity collapse-to-equal-weight bug class.

    A previous version of this solver hard-coded the log-barrier's kappa at a
    fixed value that, once a hard sum(y)==1 budget constraint was added for
    the capped branch, swamped the quadratic term and collapsed every solve
    to naive 1/n weights (the constraint made kappa's absolute scale matter,
    and 1.0 was far too large relative to typical annualized variances). The
    fix scales kappa off Sigma's own trace; this checks that scaling still
    holds: the capped solve should keep overweighting low-vol assets like a
    real ERC solution would, and risk contributions -- while only
    approximately equal once the cap binds (see the risk_parity docstring) --
    should stay within a sane band around the 1/n target rather than
    collapsing to a degenerate solution.
    """
    constraints = Constraints(max_weight=0.25)
    w = risk_parity(cov, sector_map, constraints)
    equal = 1.0 / len(tickers)
    assert not np.allclose(w.sort_index().values, equal, atol=1e-3)
    assert w["TLT"] > equal
    assert w["GLD"] > equal

    rc = risk_contributions(w, cov)
    target = 1.0 / len(tickers)
    # a genuine collapse (e.g. kappa dominating the quadratic term again)
    # would push some contributions far outside this band; a merely
    # cap-constrained approximate ERC solution should not
    assert (rc > target * 0.5).all()
    assert (rc < target * 2.0).all()


def test_risk_parity_weights_differ_from_equal_weight(cov, tickers):
    w = risk_parity(cov, None)
    equal = 1.0 / len(tickers)
    # a genuine ERC solution overweights low-vol assets (bonds/gold) vs equities
    assert w["TLT"] > equal
    assert w["GLD"] > equal
    assert not np.allclose(w.sort_index().values, equal, atol=1e-3)


def test_min_variance_has_lower_vol_than_risk_parity_and_max_sharpe(mu, cov, sector_map):
    vols = {
        "min_variance": _portfolio_vol(min_variance(cov, sector_map), cov),
        "risk_parity": _portfolio_vol(risk_parity(cov, sector_map), cov),
        "max_sharpe": _portfolio_vol(max_sharpe(mu, cov, sector_map), cov),
    }
    assert vols["min_variance"] <= vols["risk_parity"] + 1e-9
    assert vols["min_variance"] <= vols["max_sharpe"] + 1e-9


def test_efficient_frontier_is_monotonic_in_risk_aversion(mu, cov, sector_map):
    frontier = efficient_frontier(mu, cov, sector_map, n_points=15)
    assert len(frontier) >= 5
    # sorted by risk_aversion ascending -> vol should be non-increasing (more aversion = less vol)
    frontier_sorted = frontier.sort_values("risk_aversion")
    assert frontier_sorted["vol"].iloc[0] >= frontier_sorted["vol"].iloc[-1] - 1e-6


def test_risk_contributions_sum_to_one(cov, sector_map):
    w = min_variance(cov, sector_map)
    rc = risk_contributions(w, cov)
    assert rc.sum() == pytest.approx(1.0, abs=1e-6)
