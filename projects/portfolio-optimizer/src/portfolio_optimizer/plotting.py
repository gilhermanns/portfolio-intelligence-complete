"""Matplotlib chart builders. All figures are saved as SVG (plain text, git-diffable)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_PALETTE = {
    "MinVariance": "#4C72B0",
    "MaxSharpe": "#DD8452",
    "RiskParity": "#55A868",
    "BlackLitterman": "#8172B2",
    "EqualWeight": "#8C8C8C",
    "SPY": "#C44E52",
}


def plot_efficient_frontier(
    frontier: pd.DataFrame,
    highlight: dict[str, tuple[float, float]],
    out_path: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(frontier["vol"] * 100, frontier["return"] * 100, color="#4C72B0", lw=2, label="Efficient frontier")
    for name, (vol, ret) in highlight.items():
        ax.scatter(vol * 100, ret * 100, s=90, zorder=5, color=_PALETTE.get(name, "black"), label=name, edgecolor="white")
    ax.set_xlabel("Annualized volatility (%)")
    ax.set_ylabel("Annualized expected return (%)")
    ax.set_title("Efficient Frontier")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_backtest_cumulative(values: pd.DataFrame, out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for col in values.columns:
        ax.plot(values.index, values[col], label=col, color=_PALETTE.get(col, None), lw=1.6)
    ax.set_ylabel("Growth of $1")
    ax.set_title("Rolling Backtest: Strategy Comparison")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_weights_bar(weights: pd.Series, sector_map: dict[str, str], title: str, out_path: str | Path) -> None:
    order = weights.sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.tab20(np.linspace(0, 1, len(order)))
    ax.bar(order.index, order.values * 100, color=colors)
    ax.set_ylabel("Weight (%)")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_risk_contributions(rc: pd.Series, title: str, out_path: str | Path) -> None:
    order = rc.sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(order.index, order.values * 100, color="#55A868")
    ax.axhline(100 / len(order), color="black", ls="--", lw=1, label="Equal contribution")
    ax.set_ylabel("Share of portfolio risk (%)")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)
