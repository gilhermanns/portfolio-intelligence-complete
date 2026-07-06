from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .engine import Engine

PALETTE = {
    "bid": "#2E86AB",
    "ask": "#C1440E",
    "mid": "#1B1B1E",
    "lp": "#2E86AB",
    "taker": "#C1440E",
    "grid": "#D8D8D8",
}


def _style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color=PALETTE["grid"], linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def plot_mid_spread(engine: Engine, out_path: Path) -> None:
    sampler = engine.sampler
    t = np.array(sampler.t)
    mid = np.array([m if m is not None else np.nan for m in sampler.mid])
    spread = np.array([s if s is not None else np.nan for s in sampler.spread])

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t, mid, color=PALETTE["mid"], linewidth=0.9, label="mid price")
    ax.fill_between(
        t, mid - spread / 2, mid + spread / 2, color=PALETTE["bid"], alpha=0.2, label="bid/ask spread"
    )
    _style(ax)
    ax.set_xlabel("simulation time")
    ax.set_ylabel("price")
    ax.set_title("Mid-price with bid/ask spread band")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_imbalance_vs_return(engine: Engine, out_path: Path, horizon_steps: int = 4) -> None:
    sampler = engine.sampler
    mid = sampler.mid
    imb = sampler.imbalance
    xs, ys = [], []
    for i in range(len(mid) - horizon_steps):
        m0, mk, ib = mid[i], mid[i + horizon_steps], imb[i]
        if m0 is None or mk is None or ib is None or m0 == 0:
            continue
        xs.append(ib)
        ys.append((mk - m0) / m0 * 1e4)
    xs, ys = np.array(xs), np.array(ys)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(xs, ys, s=10, color=PALETTE["lp"], alpha=0.35, edgecolors="none")
    if len(xs) > 2:
        coeffs = np.polyfit(xs, ys, 1)
        xline = np.linspace(xs.min(), xs.max(), 50)
        ax.plot(xline, np.polyval(coeffs, xline), color=PALETTE["ask"], linewidth=1.8)
        corr = np.corrcoef(xs, ys)[0, 1]
        ax.text(
            0.03, 0.95, f"corr = {corr:.3f}", transform=ax.transAxes, va="top", fontsize=10
        )
    _style(ax)
    ax.set_xlabel("order-book depth imbalance (top-5 levels)")
    ax.set_ylabel(f"forward return over next {horizon_steps} samples (bps)")
    ax.set_title("Depth imbalance vs subsequent short-horizon return")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_pnl_comparison(engine: Engine, lp_id: str, taker_id: str, out_path: Path) -> None:
    sampler = engine.sampler
    t = np.array(sampler.t)
    lp_pnl = np.array(sampler.agent_pnl.get(lp_id, []))
    taker_pnl = np.array(sampler.agent_pnl.get(taker_id, []))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t[: len(lp_pnl)], lp_pnl, color=PALETTE["lp"], linewidth=1.2, label="market maker (LP) P&L")
    ax.plot(
        t[: len(taker_pnl)], taker_pnl, color=PALETTE["taker"], linewidth=1.2, label="pure taker P&L"
    )
    ax.axhline(0, color="#888888", linewidth=0.8)
    _style(ax)
    ax.set_xlabel("simulation time")
    ax.set_ylabel("mark-to-market P&L")
    ax.set_title("Market making vs pure liquidity taking, same order flow")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_execution_shortfall(shortfall_results: List[Dict], out_path: Path) -> None:
    strategies = ["aggressive", "twap"]
    means, stds = [], []
    for strat in strategies:
        vals = [
            r["shortfall_bps"]
            for r in shortfall_results
            if r["strategy"] == strat and r["shortfall_bps"] is not None
        ]
        means.append(np.mean(vals))
        stds.append(np.std(vals))

    fig, ax = plt.subplots(figsize=(6, 5))
    x = np.arange(len(strategies))
    ax.bar(
        x, means, yerr=stds, capsize=6, color=[PALETTE["taker"], PALETTE["lp"]], alpha=0.85, width=0.55
    )
    _style(ax)
    ax.set_xticks(x)
    ax.set_xticklabels(["Aggressive\n(single market order)", "TWAP\n(6 sliced market orders)"])
    ax.set_ylabel("implementation shortfall (bps)")
    ax.set_title("Execution cost: aggressive vs sliced (TWAP) parent order")
    for xi, m in zip(x, means):
        ax.text(xi, m + (max(means) * 0.03 if max(means) else 0.1), f"{m:.2f}", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)


def plot_book_ladder(engine: Engine, out_path: Path, levels: int = 8) -> None:
    d = engine.book.depth(levels)
    bids = sorted(d["bids"], key=lambda x: -x[0])
    asks = sorted(d["asks"], key=lambda x: x[0])

    fig, ax = plt.subplots(figsize=(7, 5))
    if bids:
        bid_prices = [f"{p:.2f}" for p, _ in bids]
        ax.barh(bid_prices, [q for _, q in bids], color=PALETTE["bid"], label="bids")
    if asks:
        ask_prices = [f"{p:.2f}" for p, _ in asks][::-1]
        ask_qty = [q for _, q in asks][::-1]
        ax.barh(ask_prices, [-q for q in ask_qty], color=PALETTE["ask"], label="asks")
    _style(ax)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("resting quantity (asks left, bids right)")
    ax.set_ylabel("price level")
    ax.set_title("Order book depth snapshot (end of simulation)")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, format="svg")
    plt.close(fig)
