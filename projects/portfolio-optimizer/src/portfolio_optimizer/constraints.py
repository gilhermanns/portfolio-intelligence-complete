"""Shared constraint layer used by every optimizer in this package."""

from __future__ import annotations

from dataclasses import dataclass, field

import cvxpy as cp


@dataclass
class Constraints:
    long_only: bool = True
    max_weight: float | None = None
    sector_caps: dict[str, float] | None = None
    tc_bps: float = 0.0  # one-way transaction cost, in basis points of turnover

    def validate(self, n_assets: int) -> None:
        if self.max_weight is not None and not (0.0 < self.max_weight <= 1.0):
            raise ValueError("max_weight must be in (0, 1]")
        if self.max_weight is not None and self.max_weight * n_assets < 1.0:
            raise ValueError("max_weight too small to allow weights to sum to 1")


def build_box_and_sector_constraints(
    w: cp.Variable,
    tickers: list[str],
    sector_map: dict[str, str],
    constraints: Constraints,
) -> list[cp.Constraint]:
    """Linear constraints shared by mean-variance, min-variance, and BL solves."""
    cons: list[cp.Constraint] = [cp.sum(w) == 1]
    if constraints.long_only:
        cons.append(w >= 0)
    if constraints.max_weight is not None:
        cons.append(w <= constraints.max_weight)
    if constraints.sector_caps:
        for sector, cap in constraints.sector_caps.items():
            idx = [i for i, t in enumerate(tickers) if sector_map.get(t) == sector]
            if idx:
                cons.append(cp.sum(w[idx]) <= cap)
    return cons


def turnover_cost_expr(w: cp.Variable, prev_weights, tc_bps: float):
    """Convex L1 transaction-cost term: tc_bps/1e4 * sum(|w - w_prev|)."""
    if tc_bps <= 0 or prev_weights is None:
        return 0.0
    return (tc_bps / 1e4) * cp.norm1(w - prev_weights)
