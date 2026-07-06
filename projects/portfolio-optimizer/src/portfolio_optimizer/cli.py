"""Command-line entry point: python -m portfolio_optimizer.cli --config config.yaml"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import black_litterman as bl
from . import data as data_mod
from . import plotting
from .backtest import run_backtest
from .constraints import Constraints
from .explain import explain_allocation, render_explanation
from .moments import annualized_mean_cov, daily_returns
from .optimizers import efficient_frontier, max_sharpe, min_variance, risk_contributions, risk_parity
from .universe import market_weights_for, sectors_for

OPTIMIZER_CHOICES = ["min_variance", "max_sharpe", "risk_parity", "black_litterman", "all"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Constrained portfolio optimizer CLI")
    p.add_argument("--config", default="config.yaml", help="path to a YAML config file")
    p.add_argument("--optimizer", choices=OPTIMIZER_CHOICES, default="all")
    p.add_argument("--tickers", nargs="+", default=None, help="override universe.tickers")
    p.add_argument("--max-weight", type=float, default=None, help="override constraints.max_weight")
    p.add_argument("--tc-bps", type=float, default=None, help="override constraints.tc_bps")
    p.add_argument("--output-dir", default=None, help="override output_dir")
    p.add_argument("--skip-backtest", action="store_true", help="skip the (slower) rolling backtest")
    p.add_argument("--use-cache-only", action="store_true", help="never attempt a live stooq fetch")
    return p.parse_args(argv)


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def apply_overrides(cfg: dict, args: argparse.Namespace) -> dict:
    if args.tickers:
        cfg["universe"]["tickers"] = args.tickers
    if args.max_weight is not None:
        cfg["constraints"]["max_weight"] = args.max_weight
    if args.tc_bps is not None:
        cfg["constraints"]["tc_bps"] = args.tc_bps
    if args.output_dir:
        cfg["output_dir"] = args.output_dir
    if args.use_cache_only:
        cfg["universe"]["use_cache_only"] = True
    return cfg


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = apply_overrides(load_config(args.config), args)

    tickers = cfg["universe"]["tickers"]
    sector_map = sectors_for(tickers)
    out_dir = Path(cfg.get("output_dir", "reports"))
    out_dir.mkdir(parents=True, exist_ok=True)

    prices, used_live = data_mod.load_prices(
        tickers, cfg["universe"].get("start"), cfg["universe"].get("end"), cfg["universe"].get("use_cache_only", False)
    )
    print(f"Loaded {len(prices)} daily observations for {len(tickers)} tickers "
          f"({'live stooq data' if used_live else 'bundled cached data (live fetch unavailable)'}).")

    cons_cfg = cfg.get("constraints", {})
    constraints = Constraints(
        long_only=cons_cfg.get("long_only", True),
        max_weight=cons_cfg.get("max_weight"),
        sector_caps=cons_cfg.get("sector_caps"),
        tc_bps=cons_cfg.get("tc_bps", 0.0),
    )

    returns = daily_returns(prices)
    mu, cov = annualized_mean_cov(returns)

    allocations: dict[str, pd.Series] = {}
    allocations["MinVariance"] = min_variance(cov, sector_map, constraints)
    allocations["MaxSharpe"] = max_sharpe(mu, cov, sector_map, constraints, rf=cfg.get("backtest", {}).get("rf", 0.02))
    allocations["RiskParity"] = risk_parity(cov, sector_map, constraints)

    market_weights = pd.Series(market_weights_for(tickers))
    views = [
        bl.View(assets={"AAPL": 1.0}, q=0.15, confidence=0.6),
        bl.View(
            assets={t: 1.0 / 3 for t in ("AAPL", "GOOG", "META") if t in tickers}
            | {t: -0.5 for t in ("JPM", "MA") if t in tickers},
            q=0.05,
            confidence=0.4,
        ),
        bl.View(assets={"GLD": 1.0}, q=0.03, confidence=0.3) if "GLD" in tickers else None,
    ]
    views = [v for v in views if v is not None]
    delta = cfg.get("black_litterman", {}).get("delta", 2.5)
    tau = cfg.get("black_litterman", {}).get("tau", 0.05)
    mu_bl, cov_bl = bl.posterior(cov, market_weights, views, delta=delta, tau=tau)
    allocations["BlackLitterman"] = max_sharpe(mu_bl, cov_bl, sector_map, constraints, rf=cfg.get("backtest", {}).get("rf", 0.02))

    print("\nEquilibrium (prior) vs. Black-Litterman posterior expected returns:")
    prior = bl.equilibrium_returns(cov, market_weights, delta=delta)
    print(pd.DataFrame({"prior": prior, "posterior": mu_bl}).round(4).to_string())

    selected = list(allocations) if args.optimizer == "all" else [
        {"min_variance": "MinVariance", "max_sharpe": "MaxSharpe", "risk_parity": "RiskParity", "black_litterman": "BlackLitterman"}[args.optimizer]
    ]

    for name in selected:
        w = allocations[name]
        mu_for_explain = mu_bl if name == "BlackLitterman" else mu
        table = explain_allocation(w, mu_for_explain, cov, sector_map)
        print(f"\n=== {name} ===")
        print(render_explanation(table))
        plotting.plot_weights_bar(w, sector_map, f"{name} Allocation", out_dir / f"weights_{name}.svg")
        rc = risk_contributions(w, cov)
        plotting.plot_risk_contributions(rc, f"{name} Risk Contributions", out_dir / f"risk_contrib_{name}.svg")

    print("\nBuilding efficient frontier...")
    frontier = efficient_frontier(mu, cov, sector_map, constraints, n_points=25)
    highlight = {}
    for name in ("MinVariance", "MaxSharpe", "RiskParity", "BlackLitterman"):
        w = allocations[name]
        ret = float(mu.reindex(cov.columns) @ w)
        vol = float(np.sqrt(w.values @ cov.values @ w.values))
        highlight[name] = (vol, ret)
    plotting.plot_efficient_frontier(frontier, highlight, out_dir / "efficient_frontier.svg")
    frontier.to_csv(out_dir / "efficient_frontier.csv", index=False)

    if not args.skip_backtest:
        print("\nRunning rolling monthly backtest (this takes a minute)...")
        bt_cfg = cfg.get("backtest", {})
        result = run_backtest(
            prices[tickers],
            sector_map,
            prices["SPY"] if "SPY" in prices.columns else prices.iloc[:, 0],
            window_months=bt_cfg.get("window_months", 30),
            tc_bps=constraints.tc_bps,
            max_weight=constraints.max_weight,
            sector_caps=constraints.sector_caps,
            rf=bt_cfg.get("rf", 0.02),
        )
        metrics = result.metrics(rf=bt_cfg.get("rf", 0.02))
        print("\nBacktest metrics:")
        print(metrics.round(4).to_string())
        metrics.to_csv(out_dir / "backtest_metrics.csv")
        result.values.to_csv(out_dir / "backtest_values.csv")
        plotting.plot_backtest_cumulative(result.values, out_dir / "backtest_cumulative.svg")

    print(f"\nArtifacts written to {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
