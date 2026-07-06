import pytest

from portfolio_optimizer.explain import explain_allocation, render_explanation
from portfolio_optimizer.optimizers import min_variance


def test_explain_table_contribution_columns_are_consistent(mu, cov, sector_map):
    w = min_variance(cov, sector_map)
    table = explain_allocation(w, mu, cov, sector_map)
    assert table["weight"].sum() == pytest.approx(1.0, abs=1e-4)
    assert table["risk_contribution_pct"].sum() == pytest.approx(1.0, abs=1e-4)
    # return contributions are additive: sum(w_i * mu_i) == portfolio expected return
    port_return = float((w.reindex(cov.columns) * mu.reindex(cov.columns)).sum())
    assert table["return_contribution"].sum() == pytest.approx(port_return, abs=1e-6)


def test_render_explanation_lists_every_asset(mu, cov, sector_map, tickers):
    w = min_variance(cov, sector_map)
    table = explain_allocation(w, mu, cov, sector_map)
    text = render_explanation(table)
    for ticker in tickers:
        assert ticker in text
