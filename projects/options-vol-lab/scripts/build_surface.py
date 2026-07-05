#!/usr/bin/env python
"""Build a synthetic Heston implied-vol surface via Monte Carlo, plot it, then
calibrate a Heston model back to that surface and report parameter recovery.

No live market data is used: the "market" here is a Heston process with
parameters chosen up front and known to us, simulated via Monte Carlo, with
implied vols inverted from the simulated option prices. This lets calibration
be checked as a clean round trip (recovered params vs. the seeded ones)
instead of trusting an opaque fit to real quotes.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from options_vol_lab.heston.calibrate import HestonParams, calibrate_heston
from options_vol_lab.heston.pricer import heston_price
from options_vol_lab.implied_vol import implied_volatility
from options_vol_lab.surface import build_synthetic_surface

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

# Palette per the project's dataviz convention: one sequential hue (blue) for
# magnitude, a fixed categorical order for discrete series.
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CATEGORICAL = ["#2a78d6", "#1baf7a", "#eda100", "#4a3aa7", "#e34948", "#eb6834"]
INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"


def _style_axes(ax):
    ax.set_facecolor("#fcfcfb")
    ax.tick_params(colors=SECONDARY_INK, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(MUTED)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def plot_heatmap(surface, path):
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
    im = ax.imshow(surface.ivs, aspect="auto", cmap=cmap, origin="lower")
    ax.set_xticks(range(len(surface.moneyness)))
    ax.set_xticklabels([f"{m:.2f}" for m in surface.moneyness])
    ax.set_yticks(range(len(surface.maturities)))
    ax.set_yticklabels([f"{t:.2f}y" for t in surface.maturities])
    ax.set_xlabel("Moneyness (K / S)", color=SECONDARY_INK)
    ax.set_ylabel("Maturity", color=SECONDARY_INK)
    ax.set_title("Synthetic implied-vol surface (Heston MC)", color=INK, fontsize=12, pad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Implied vol", color=SECONDARY_INK)
    cbar.ax.tick_params(colors=SECONDARY_INK)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def plot_smile(surface, path):
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    _style_axes(ax)
    for i, t in enumerate(surface.maturities):
        color = CATEGORICAL[i % len(CATEGORICAL)]
        ax.plot(surface.moneyness, surface.ivs[i], color=color, linewidth=2,
                marker="o", markersize=4, label=f"T = {t:.2f}y")
    ax.set_xlabel("Moneyness (K / S)", color=SECONDARY_INK)
    ax.set_ylabel("Implied vol", color=SECONDARY_INK)
    ax.set_title("Volatility smile by maturity", color=INK, fontsize=12, pad=10)
    legend = ax.legend(frameon=False, fontsize=9, labelcolor=SECONDARY_INK)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def plot_term_structure(surface, path, moneyness_levels=(0.9, 1.0, 1.1)):
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    _style_axes(ax)
    for i, level in enumerate(moneyness_levels):
        idx = int(np.argmin(np.abs(surface.moneyness - level)))
        color = CATEGORICAL[i % len(CATEGORICAL)]
        ax.plot(surface.maturities, surface.ivs[:, idx], color=color, linewidth=2,
                marker="o", markersize=4, label=f"K/S = {surface.moneyness[idx]:.2f}")
    ax.set_xlabel("Maturity (years)", color=SECONDARY_INK)
    ax.set_ylabel("Implied vol", color=SECONDARY_INK)
    ax.set_title("Volatility term structure by moneyness", color=INK, fontsize=12, pad=10)
    ax.legend(frameon=False, fontsize=9, labelcolor=SECONDARY_INK)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def plot_calibration_fit(surface, fitted, spot, rate, path):
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    _style_axes(ax)
    mid = len(surface.maturities) // 2
    for i in (0, mid, len(surface.maturities) - 1):
        t = surface.maturities[i]
        color = CATEGORICAL[i % len(CATEGORICAL)]
        ax.plot(surface.moneyness, surface.ivs[i], "o", color=color, markersize=5,
                label=f"MC market, T={t:.2f}y")
        fitted_ivs = []
        for strike in surface.strikes:
            price = heston_price(spot, strike, rate, t, fitted.kappa, fitted.theta,
                                  fitted.sigma_v, fitted.rho, fitted.v0, "call")
            fitted_ivs.append(implied_volatility(price, spot, strike, rate, t, "call"))
        ax.plot(surface.moneyness, fitted_ivs, "-", color=color, linewidth=1.8,
                label=f"Calibrated fit, T={t:.2f}y")
    ax.set_xlabel("Moneyness (K / S)", color=SECONDARY_INK)
    ax.set_ylabel("Implied vol", color=SECONDARY_INK)
    ax.set_title("Calibrated Heston model vs. synthetic market", color=INK, fontsize=12, pad=10)
    ax.legend(frameon=False, fontsize=8, labelcolor=SECONDARY_INK, ncol=1)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def main():
    REPORTS_DIR.mkdir(exist_ok=True)

    true_params = dict(kappa=2.0, theta=0.045, sigma_v=0.55, rho=-0.65, v0=0.05)
    spot, rate = 100.0, 0.03
    moneyness_grid = np.array([0.80, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20])
    maturities = np.array([0.25, 0.5, 1.0, 1.5, 2.0])

    print("Building synthetic Heston MC surface...")
    t0 = time.time()
    surface = build_synthetic_surface(
        spot, rate, moneyness_grid=moneyness_grid, maturities=maturities,
        n_paths=200_000, n_steps_per_year=100, seed=7, **true_params,
    )
    build_time = time.time() - t0
    print(f"  done in {build_time:.1f}s")
    print(surface.ivs)

    plot_heatmap(surface, REPORTS_DIR / "vol_surface_heatmap.svg")
    plot_smile(surface, REPORTS_DIR / "vol_smile.svg")
    plot_term_structure(surface, REPORTS_DIR / "vol_term_structure.svg")

    print("Calibrating Heston model to the synthetic MC surface...")
    initial_guess = HestonParams(kappa=1.0, theta=0.06, sigma_v=0.3, rho=-0.3, v0=0.03)
    t0 = time.time()
    fitted, result = calibrate_heston(surface.strikes, surface.maturities, surface.ivs,
                                       spot, rate, initial_guess)
    calib_time = time.time() - t0
    print(f"  done in {calib_time:.1f}s, nfev={result.nfev}, cost={result.cost:.6e}")

    plot_calibration_fit(surface, fitted, spot, rate, REPORTS_DIR / "calibration_fit.svg")

    rows = []
    for name in ("kappa", "theta", "sigma_v", "rho", "v0"):
        true_v = true_params[name]
        fit_v = getattr(fitted, name)
        rel_err = abs(fit_v - true_v) / abs(true_v)
        rows.append((name, true_v, fit_v, rel_err))

    lines = []
    lines.append("Heston calibration round-trip (synthetic Monte Carlo market)")
    lines.append("=" * 62)
    lines.append(f"Surface build time: {build_time:.1f}s ({len(maturities)} maturities x "
                 f"{len(moneyness_grid)} strikes, 200,000 MC paths each)")
    lines.append(f"Calibration time: {calib_time:.1f}s, nfev={result.nfev}, "
                 f"final cost={result.cost:.6e}")
    lines.append("")
    lines.append(f"{'param':<10}{'seeded':>12}{'fitted':>12}{'rel. error':>14}")
    for name, true_v, fit_v, rel_err in rows:
        lines.append(f"{name:<10}{true_v:>12.4f}{fit_v:>12.4f}{rel_err:>13.2%}")
    report = "\n".join(lines)
    print(report)
    (REPORTS_DIR / "heston_calibration.txt").write_text(report + "\n")

    summary = {
        "true_params": true_params,
        "fitted_params": {n: getattr(fitted, n) for n in true_params},
        "build_time_sec": build_time,
        "calib_time_sec": calib_time,
        "nfev": result.nfev,
        "final_cost": result.cost,
        "moneyness_grid": moneyness_grid.tolist(),
        "maturities": maturities.tolist(),
        "ivs": surface.ivs.tolist(),
    }
    (REPORTS_DIR / "surface_results.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
