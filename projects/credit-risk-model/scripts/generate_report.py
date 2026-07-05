"""Trains all models, computes every metric in the README, and renders the report charts.

Run with: python scripts/generate_report.py
Writes SVGs to reports/ and prints a metrics summary (also saved as reports/metrics.json)
so the numbers embedded in the README come from one real, reproducible run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from credit_risk_model.data import FEATURE_COLUMNS, TARGET_COLUMN, apply_macro_shock  # noqa: E402
from credit_risk_model.expected_loss import (  # noqa: E402
    assign_lgd_ead,
    expected_loss_point_estimate,
    simulate_portfolio_losses,
)
from credit_risk_model.explain import build_linear_explainer, compute_shap_values, global_importance  # noqa: E402
from credit_risk_model.features import feature_names_out  # noqa: E402
from credit_risk_model.metrics import compute_discrimination_metrics, confusion_at_threshold, reliability_curve  # noqa: E402
from credit_risk_model.pipeline import train_all  # noqa: E402
from credit_risk_model.segments import segment_report  # noqa: E402

REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# --- palette (validated categorical order; see dataviz skill reference) ---
BLUE = "#2a78d6"
AQUA = "#1baf7a"
YELLOW = "#eda100"
RED = "#e34948"
INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": SECONDARY_INK,
        "ytick.color": SECONDARY_INK,
        "grid.color": GRID,
        "font.size": 11,
        "axes.grid": True,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.facecolor": SURFACE,
    }
)


def savefig(fig, name: str) -> None:
    path = REPORTS_DIR / name
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path.relative_to(REPO_ROOT)}")


def main() -> None:
    seed = 42
    artifacts = train_all(n=20_000, seed=seed)
    df = artifacts.df
    test_df = df.loc[artifacts.test_idx]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET_COLUMN].to_numpy()

    logistic = artifacts.logistic_pipeline
    gbm = artifacts.gbm_pipeline

    raw_pd_test = logistic.predict_proba(X_test)[:, 1]
    gbm_pd_test = gbm.predict_proba(X_test)[:, 1]
    sigmoid_pd_test = artifacts.calibrator_sigmoid.predict_proba(X_test)[:, 1]
    isotonic_pd_test = artifacts.calibrator_isotonic.predict_proba(X_test)[:, 1]

    metrics = {
        "n_total": len(df),
        "n_train": len(artifacts.train_idx),
        "n_calib": len(artifacts.calib_idx),
        "n_test": len(artifacts.test_idx),
        "default_rate_overall": float(df[TARGET_COLUMN].mean()),
        "logistic_raw": compute_discrimination_metrics(y_test, raw_pd_test).as_dict(),
        "gbm": compute_discrimination_metrics(y_test, gbm_pd_test).as_dict(),
        "logistic_sigmoid_calibrated": compute_discrimination_metrics(y_test, sigmoid_pd_test).as_dict(),
        "logistic_isotonic_calibrated": compute_discrimination_metrics(y_test, isotonic_pd_test).as_dict(),
        "majority_class_baseline_brier": float(np.mean((y_test - y_test.mean()) ** 2)),
    }

    threshold = 0.20
    metrics["confusion_at_threshold_isotonic"] = confusion_at_threshold(y_test, isotonic_pd_test, threshold)

    print(json.dumps(metrics, indent=2))

    # --- Chart 1: ROC + PR curves, logistic vs GBM ---
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    fpr_lr, tpr_lr, _ = roc_curve(y_test, raw_pd_test)
    fpr_gbm, tpr_gbm, _ = roc_curve(y_test, gbm_pd_test)
    axes[0].plot(fpr_lr, tpr_lr, color=BLUE, lw=2, label=f"Logistic (AUC {metrics['logistic_raw']['roc_auc']:.3f})")
    axes[0].plot(fpr_gbm, tpr_gbm, color=AQUA, lw=2, label=f"GBM (AUC {metrics['gbm']['roc_auc']:.3f})")
    axes[0].plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--")
    axes[0].set_xlabel("False positive rate")
    axes[0].set_ylabel("True positive rate")
    axes[0].set_title("ROC curve", loc="left", fontsize=12)
    axes[0].legend(frameon=False, loc="lower right", fontsize=9)

    prec_lr, rec_lr, _ = precision_recall_curve(y_test, raw_pd_test)
    prec_gbm, rec_gbm, _ = precision_recall_curve(y_test, gbm_pd_test)
    axes[1].plot(rec_lr, prec_lr, color=BLUE, lw=2, label=f"Logistic (PR-AUC {metrics['logistic_raw']['pr_auc']:.3f})")
    axes[1].plot(rec_gbm, prec_gbm, color=AQUA, lw=2, label=f"GBM (PR-AUC {metrics['gbm']['pr_auc']:.3f})")
    axes[1].axhline(y_test.mean(), color=MUTED, lw=1, ls="--", label=f"Base rate ({y_test.mean():.2%})")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-recall curve", loc="left", fontsize=12)
    axes[1].legend(frameon=False, loc="upper right", fontsize=9)
    fig.suptitle("Logistic regression vs. gradient-boosted trees (held-out test set)", fontsize=12, y=1.03)
    savefig(fig, "roc_pr_curves.svg")

    # --- Chart 2: calibration reliability diagram ---
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--", label="Perfect calibration")
    for scores, color, label in [
        (raw_pd_test, RED, "Uncalibrated logistic"),
        (sigmoid_pd_test, YELLOW, "Platt (sigmoid) calibrated"),
        (isotonic_pd_test, BLUE, "Isotonic calibrated"),
    ]:
        mean_pred, obs_freq, counts = reliability_curve(y_test, scores, n_bins=10)
        valid = ~np.isnan(mean_pred)
        ax.plot(mean_pred[valid], obs_freq[valid], marker="o", ms=5, lw=2, color=color, label=label)
    ax.set_xlabel("Mean predicted PD (bin)")
    ax.set_ylabel("Observed default rate (bin)")
    ax.set_title("Calibration: before vs. after", loc="left", fontsize=12)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    savefig(fig, "calibration_curve.svg")

    # --- Chart 3: SHAP global importance ---
    train_df = df.loc[artifacts.train_idx]
    background = train_df[FEATURE_COLUMNS].sample(n=500, random_state=seed)
    explainer, _ = build_linear_explainer(logistic, background)
    shap_values = compute_shap_values(logistic, explainer, X_test)
    feature_names = feature_names_out(logistic.named_steps["preprocess"])
    importance = global_importance(shap_values, feature_names).head(12).iloc[::-1]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.barh(importance["feature"], importance["mean_abs_shap"], color=BLUE, height=0.65)
    ax.set_xlabel("Mean |SHAP value| (logit scale)")
    ax.set_title("Global feature importance (logistic PD model)", loc="left", fontsize=12)
    savefig(fig, "shap_importance.svg")

    # --- Segment report (table, not chart) ---
    seg_df = test_df.copy()
    seg_df["pd_isotonic"] = isotonic_pd_test
    segments = segment_report(seg_df, TARGET_COLUMN, "pd_isotonic", "loan_purpose")
    metrics["segment_report"] = segments.to_dict(orient="records")

    # --- Expected loss simulation: base vs. stress ---
    rng = np.random.default_rng(seed)
    pd_full = artifacts.calibrator_isotonic.predict_proba(df[FEATURE_COLUMNS])[:, 1]
    lgd, ead = assign_lgd_ead(df, rng)
    el_point = expected_loss_point_estimate(pd_full, lgd, ead)

    n_sims = 2000
    base_losses = simulate_portfolio_losses(pd_full, df["loan_purpose"].to_numpy(), df["income"].to_numpy(), n_sims, rng)

    shocked_df = apply_macro_shock(df, unemployment_delta=4.0)
    pd_shocked = artifacts.calibrator_isotonic.predict_proba(shocked_df[FEATURE_COLUMNS])[:, 1]
    stress_losses = simulate_portfolio_losses(
        pd_shocked, df["loan_purpose"].to_numpy(), df["income"].to_numpy(), n_sims, rng
    )

    metrics["expected_loss"] = {
        "point_estimate_total": float(el_point.sum()),
        "mc_base_mean": float(base_losses.mean()),
        "mc_base_p95": float(np.percentile(base_losses, 95)),
        "mc_base_p99": float(np.percentile(base_losses, 99)),
        "mc_stress_mean": float(stress_losses.mean()),
        "mc_stress_p95": float(np.percentile(stress_losses, 95)),
        "mc_stress_p99": float(np.percentile(stress_losses, 99)),
        "stress_unemployment_delta_pp": 4.0,
    }

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(base_losses, bins=40, color=BLUE, alpha=0.75, label=f"Base scenario (mean ${base_losses.mean():,.0f})")
    ax.hist(
        stress_losses, bins=40, color=RED, alpha=0.6, label=f"Stress: +4pp unemployment (mean ${stress_losses.mean():,.0f})"
    )
    ax.set_xlabel("Simulated portfolio annual loss ($)")
    ax.set_ylabel("Simulated years (count)")
    ax.set_title("Monte Carlo portfolio expected-loss distribution", loc="left", fontsize=12)
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    savefig(fig, "expected_loss_distribution.svg")

    with open(REPORTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"wrote {(REPORTS_DIR / 'metrics.json').relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
