"""Turn an optimizer's weight vector into a human-readable allocation rationale."""

from __future__ import annotations

import pandas as pd

from .optimizers import risk_contributions


def explain_allocation(weights: pd.Series, mu: pd.Series, cov: pd.DataFrame, sector_map: dict[str, str]) -> pd.DataFrame:
    """Per-asset table of weight, expected-return contribution, and risk contribution.

    Return contribution is simply w_i * mu_i (additive by construction).
    Risk contribution is w_i * (Sigma w)_i / portfolio variance (also additive,
    Euler's theorem for the variance's homogeneity of degree 2 in weights).
    """
    tickers = list(cov.columns)
    w = weights.reindex(tickers).fillna(0)
    mu_r = mu.reindex(tickers).fillna(0)
    port_return = float(w @ mu_r)
    rc = risk_contributions(w, cov)

    table = pd.DataFrame(
        {
            "weight": w,
            "sector": [sector_map.get(t, "Other") for t in tickers],
            "expected_return": mu_r,
            "return_contribution": w * mu_r,
            "return_contribution_pct": (w * mu_r) / port_return if port_return != 0 else 0.0,
            "risk_contribution_pct": rc,
        }
    )
    return table.sort_values("weight", ascending=False)


def render_explanation(table: pd.DataFrame) -> str:
    lines = ["Allocation rationale (sorted by weight):", ""]
    for ticker, row in table.iterrows():
        lines.append(
            f"  {ticker:6s} ({row['sector']:<24s}) weight={row['weight']*100:5.1f}%  "
            f"exp.return={row['expected_return']*100:6.2f}%/yr  "
            f"contributes {row['return_contribution_pct']*100:5.1f}% of portfolio return, "
            f"{row['risk_contribution_pct']*100:5.1f}% of portfolio risk"
        )
    return "\n".join(lines)
