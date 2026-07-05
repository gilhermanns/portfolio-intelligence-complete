import numpy as np
import pytest

from credit_risk_model.metrics import confusion_at_threshold, ks_statistic, reliability_curve


def test_ks_statistic_perfect_separation_is_one():
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_score = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
    assert ks_statistic(y_true, y_score) == pytest.approx(1.0)


def test_ks_statistic_no_separation_is_zero():
    # identical score distributions for both classes -> KS should be ~0
    y_true = np.array([0, 1] * 50)
    rng = np.random.default_rng(0)
    y_score = rng.uniform(0, 1, size=100)
    # shuffle so score is independent of label
    y_score = rng.permutation(y_score)
    assert ks_statistic(y_true, y_score) < 0.25


def test_ks_statistic_hand_computed_example():
    # goods: scores [0.1, 0.2, 0.3, 0.4]; bads: scores [0.3, 0.4, 0.5, 0.6]
    # at threshold 0.3: TPR = P(bad score <= 0.3)... use ROC-based definition,
    # hand-verified via cumulative distributions below.
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_score = np.array([0.1, 0.2, 0.3, 0.4, 0.3, 0.4, 0.5, 0.6])
    goods = np.sort(y_score[y_true == 0])
    bads = np.sort(y_score[y_true == 1])
    grid = np.unique(y_score)
    cdf_good = np.array([(goods <= t).mean() for t in grid])
    cdf_bad = np.array([(bads <= t).mean() for t in grid])
    expected_ks = float(np.max(np.abs(cdf_bad - cdf_good)))
    assert ks_statistic(y_true, y_score) == pytest.approx(expected_ks, abs=1e-9)


def test_ks_statistic_requires_both_classes():
    with pytest.raises(ValueError):
        ks_statistic(np.array([0, 0, 0]), np.array([0.1, 0.2, 0.3]))


def test_confusion_at_threshold_counts():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_score = np.array([0.05, 0.15, 0.5, 0.4, 0.6, 0.9])
    result = confusion_at_threshold(y_true, y_score, threshold=0.5)
    # declined (score >= 0.5): indices 2 (good), 4 (bad), 5 (bad) -> fp=1, tp=2
    # approved (score < 0.5): indices 0,1 (good), 3 (bad) -> tn=2, fn=1
    assert result["tp"] == 2
    assert result["fp"] == 1
    assert result["tn"] == 2
    assert result["fn"] == 1
    assert result["decline_rate"] == pytest.approx(3 / 6)


def test_reliability_curve_bins_match_counts():
    y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    y_score = np.array([0.05, 0.05, 0.15, 0.15, 0.85, 0.85, 0.95, 0.95])
    mean_pred, obs_freq, counts = reliability_curve(y_true, y_score, n_bins=10)
    assert counts.sum() == len(y_true)
    valid = counts > 0
    assert np.all(obs_freq[valid] == 0.5)
