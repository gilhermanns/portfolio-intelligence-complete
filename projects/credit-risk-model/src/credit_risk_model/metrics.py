"""Credit-risk evaluation metrics: discrimination, calibration, and business-rule confusion matrix."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)


def ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Kolmogorov-Smirnov statistic: max separation between the good/bad cumulative score distributions.

    This is the standard credit-scoring discrimination metric alongside AUC:
    KS = max_t |CDF(score | default=1)(t) - CDF(score | default=0)(t)|,
    computed here via the ROC curve identity KS = max(TPR - FPR).
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        raise ValueError("KS statistic requires both classes present in y_true")
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(tpr - fpr))


@dataclass
class DiscriminationMetrics:
    roc_auc: float
    pr_auc: float
    ks: float
    brier: float

    def as_dict(self) -> dict:
        return {"roc_auc": self.roc_auc, "pr_auc": self.pr_auc, "ks": self.ks, "brier": self.brier}


def compute_discrimination_metrics(y_true: np.ndarray, y_score: np.ndarray) -> DiscriminationMetrics:
    return DiscriminationMetrics(
        roc_auc=float(roc_auc_score(y_true, y_score)),
        pr_auc=float(average_precision_score(y_true, y_score)),
        ks=ks_statistic(y_true, y_score),
        brier=float(brier_score_loss(y_true, y_score)),
    )


def confusion_at_threshold(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict:
    """Confusion matrix and business metrics for a decline/refer/approve cutoff.

    ``threshold`` is the PD above which a loan is declined; this mirrors an
    underwriting cutoff rule rather than the default 0.5 classifier threshold.
    """
    y_pred = (np.asarray(y_score) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    total = tn + fp + fn + tp
    return {
        "threshold": threshold,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "decline_rate": float((tp + fp) / total),
        "precision_declined_are_bad": float(tp / (tp + fp)) if (tp + fp) > 0 else float("nan"),
        "recall_bad_caught": float(tp / (tp + fn)) if (tp + fn) > 0 else float("nan"),
        "false_decline_rate_of_good": float(fp / (fp + tn)) if (fp + tn) > 0 else float("nan"),
    }


def reliability_curve(y_true: np.ndarray, y_score: np.ndarray, n_bins: int = 10) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mean predicted probability and observed frequency per equal-width bin, for a calibration plot."""
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.asarray(y_score, dtype=float)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(y_score, bin_edges[1:-1], right=True), 0, n_bins - 1)

    mean_pred = np.full(n_bins, np.nan)
    obs_freq = np.full(n_bins, np.nan)
    counts = np.zeros(n_bins, dtype=int)
    for b in range(n_bins):
        mask = bin_idx == b
        counts[b] = mask.sum()
        if counts[b] > 0:
            mean_pred[b] = y_score[mask].mean()
            obs_freq[b] = y_true[mask].mean()
    return mean_pred, obs_freq, counts
