"""Segment-level (loan purpose) breakdowns of PD accuracy and calibration."""

from __future__ import annotations

import numpy as np
import pandas as pd

from credit_risk_model.metrics import compute_discrimination_metrics


def segment_report(df: pd.DataFrame, y_true_col: str, y_score_col: str, segment_col: str = "loan_purpose") -> pd.DataFrame:
    """Per-segment observed default rate, mean predicted PD, and discrimination metrics."""
    rows = []
    for segment, group in df.groupby(segment_col, observed=True):
        y_true = group[y_true_col].to_numpy()
        y_score = group[y_score_col].to_numpy()
        row = {
            "segment": segment,
            "n": len(group),
            "observed_default_rate": float(y_true.mean()),
            "mean_predicted_pd": float(y_score.mean()),
        }
        if y_true.sum() > 0 and y_true.sum() < len(y_true):
            metrics = compute_discrimination_metrics(y_true, y_score)
            row.update(metrics.as_dict())
        else:
            row.update({"roc_auc": np.nan, "pr_auc": np.nan, "ks": np.nan, "brier": np.nan})
        rows.append(row)
    return pd.DataFrame(rows).sort_values("observed_default_rate", ascending=False).reset_index(drop=True)
