"""Convex portfolio optimizers: mean-variance, minimum-variance, risk parity.

All solvers return a pandas Series of weights indexed by ticker. Optional
``prev_weights`` + ``constraints.tc_bps`` add a turnover-penalty term to the
objective so that rolling re-optimization (see backtest.py) does not chase
noise between rebalances.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import cvxpy as cp

from .constraints import Constraints, build_box_and_sector_constraints, turnover_cost_expr


class OptimizationError(RuntimeError):
    pass


def _solve(problem: cp.Problem) -> None:
    for solver in (cp.CLARABEL, cp.ECOS, cp.SCS):
        try:
            problem.solve(solver=solver)
        except (cp.error.SolverError, cp.error.DCPError):
            continue
        if problem.status in ("optimal", "optimal_inaccurate"):
            return
    raise OptimizationError(f"solver failed to converge, status={problem.status}")


def _weights_series(w: cp.Variable, tickers: list[str]) -> pd.Series:
    values = np.asarray(w.value).flatten()
    values = np.clip(values, 0, None) if values.min() > -1e-6 else values
    values = values / values.sum()
    return pd.Series(values, index=tickers)


def min_variance(
    cov: pd.DataFrame,
    sector_map: dict[str, str],
    constraints: Constraints | None = None,
    prev_weights: pd.Series | None = None,
) -> pd.Series:
    tickers = list(cov.columns)
    constraints = constraints or Constraints()
    constraints.validate(len(tickers))
    w = cp.Variable(len(tickers))
    Sigma = cov.values
    prev = prev_weights.reindex(tickers).fillna(0).values if prev_weights is not None else None
    cost = turnover_cost_expr(w, prev, constraints.tc_bps)
    objective = cp.Minimize(cp.quad_form(w, cp.psd_wrap(Sigma)) + cost)
    cons = build_box_and_sector_constraints(w, tickers, sector_map, constraints)
    _solve(cp.Problem(objective, cons))
    return _weights_series(w, tickers)


def mean_variance(
    mu: pd.Series,
    cov: pd.DataFrame,
    sector_map: dict[str, str],
    risk_aversion: float = 3.0,
    constraints: Constraints | None = None,
    prev_weights: pd.Series | None = None,
) -> pd.Series:
    """Maximize mu'w - (risk_aversion/2) * w'Sigma w, i.e. a point on the frontier.

    risk_aversion trades expected return off against variance; higher values
    push the solution toward the minimum-variance end of the frontier.
    """
    tickers = list(cov.columns)
    constraints = constraints or Constraints()
    constraints.validate(len(tickers))
    w = cp.Variable(len(tickers))
    Sigma = cov.values
    mu_arr = mu.reindex(tickers).values
    prev = prev_weights.reindex(tickers).fillna(0).values if prev_weights is not None else None
    cost = turnover_cost_expr(w, prev, constraints.tc_bps)
    objective = cp.Maximize(mu_arr @ w - 0.5 * risk_aversion * cp.quad_form(w, cp.psd_wrap(Sigma)) - cost)
    cons = build_box_and_sector_constraints(w, tickers, sector_map, constraints)
    _solve(cp.Problem(objective, cons))
    return _weights_series(w, tickers)


def max_sharpe(
    mu: pd.Series,
    cov: pd.DataFrame,
    sector_map: dict[str, str],
    constraints: Constraints | None = None,
    rf: float = 0.02,
    prev_weights: pd.Series | None = None,
) -> pd.Series:
    """Tangency portfolio via bisection over risk_aversion to hit max Sharpe."""
    tickers = list(cov.columns)
    best_w, best_sharpe = None, -np.inf
    for ra in np.geomspace(0.1, 200, 40):
        try:
            w = mean_variance(mu, cov, sector_map, risk_aversion=ra, constraints=constraints, prev_weights=prev_weights)
        except OptimizationError:
            continue
        ret = float(mu.reindex(tickers) @ w)
        vol = float(np.sqrt(w.values @ cov.values @ w.values))
        sharpe = (ret - rf) / vol if vol > 1e-10 else -np.inf
        if sharpe > best_sharpe:
            best_sharpe, best_w = sharpe, w
    if best_w is None:
        raise OptimizationError("max_sharpe: no feasible risk_aversion grid point converged")
    return best_w


def risk_parity(
    cov: pd.DataFrame,
    sector_map: dict[str, str] | None = None,
    constraints: Constraints | None = None,
    kappa: float | None = None,
) -> pd.Series:
    """Equal (or constrained near-equal) risk contribution portfolio.

    Convex reformulation (Spinu 2013 / Roncalli): minimize
    0.5 y'Sigma y - kappa * sum(log(y_i)) over y > 0, with NO budget
    constraint. The first-order condition y_i*(Sigma y)_i = kappa for every i
    is exactly the equal-risk-contribution condition, and it holds for any
    kappa > 0 since rescaling y rescales kappa by a matching factor -- so the
    normalized w = y / sum(y) is independent of kappa. This only holds
    without extra linear constraints; box/sector caps require anchoring the
    scale with sum(w) == 1, which makes kappa's magnitude matter again, so in
    that branch kappa is set relative to Sigma's own scale to avoid the
    barrier term either vanishing or swamping the quadratic term.
    """
    tickers = list(cov.columns)
    constraints = constraints or Constraints()
    n = len(tickers)
    Sigma = cov.values
    has_caps = constraints.max_weight is not None or (constraints.sector_caps and sector_map)

    y = cp.Variable(n)
    if not has_caps:
        k = kappa if kappa is not None else 1.0
        objective = cp.Minimize(0.5 * cp.quad_form(y, cp.psd_wrap(Sigma)) - k * cp.sum(cp.log(y)))
        cons = [y >= 1e-8]
        _solve(cp.Problem(objective, cons))
        return _weights_series(y, tickers)

    k = kappa if kappa is not None else float(np.trace(Sigma) / n) * 1e-2
    objective = cp.Minimize(0.5 * cp.quad_form(y, cp.psd_wrap(Sigma)) - k * cp.sum(cp.log(y)))
    cons = [cp.sum(y) == 1, y >= 1e-8]
    if constraints.max_weight is not None:
        cons.append(y <= constraints.max_weight)
    if constraints.sector_caps and sector_map:
        for sector, cap in constraints.sector_caps.items():
            idx = [i for i, t in enumerate(tickers) if sector_map.get(t) == sector]
            if idx:
                cons.append(cp.sum(y[idx]) <= cap)
    _solve(cp.Problem(objective, cons))
    return _weights_series(y, tickers)


def risk_contributions(weights: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """Each asset's contribution to total portfolio variance, w_i * (Sigma w)_i, normalized to sum to 1."""
    w = weights.reindex(cov.columns).values
    marginal = cov.values @ w
    contrib = w * marginal
    return pd.Series(contrib / contrib.sum(), index=cov.columns)


def efficient_frontier(
    mu: pd.Series,
    cov: pd.DataFrame,
    sector_map: dict[str, str],
    constraints: Constraints | None = None,
    n_points: int = 25,
) -> pd.DataFrame:
    rows = []
    for ra in np.geomspace(0.05, 500, n_points):
        try:
            w = mean_variance(mu, cov, sector_map, risk_aversion=ra, constraints=constraints)
        except OptimizationError:
            continue
        ret = float(mu.reindex(cov.columns) @ w)
        vol = float(np.sqrt(w.values @ cov.values @ w.values))
        rows.append({"risk_aversion": ra, "return": ret, "vol": vol, **w.to_dict()})
    return pd.DataFrame(rows).drop_duplicates(subset=["return", "vol"])
