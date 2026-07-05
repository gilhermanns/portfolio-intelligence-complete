import pandas as pd
import pytest

from credit_risk_model.segments import segment_report


def test_segment_report_groups_and_computes_rates():
    df = pd.DataFrame(
        {
            "loan_purpose": ["a", "a", "a", "b", "b", "b"],
            "default": [1, 0, 0, 0, 0, 1],
            "score": [0.8, 0.2, 0.3, 0.1, 0.2, 0.9],
        }
    )
    report = segment_report(df, "default", "score", "loan_purpose")
    assert set(report["segment"]) == {"a", "b"}
    row_a = report[report["segment"] == "a"].iloc[0]
    row_b = report[report["segment"] == "b"].iloc[0]
    assert row_a["n"] == 3
    assert row_a["observed_default_rate"] == pytest.approx(1 / 3)
    assert row_b["observed_default_rate"] == pytest.approx(1 / 3)
    assert row_a["mean_predicted_pd"] == pytest.approx((0.8 + 0.2 + 0.3) / 3)


def test_segment_report_sorted_by_default_rate_descending():
    df = pd.DataFrame(
        {
            "loan_purpose": ["low"] * 4 + ["high"] * 4,
            "default": [0, 0, 0, 1] + [1, 1, 0, 1],
            "score": [0.1, 0.2, 0.1, 0.6] + [0.7, 0.8, 0.3, 0.9],
        }
    )
    report = segment_report(df, "default", "score", "loan_purpose")
    assert report.iloc[0]["segment"] == "high"
    assert report.iloc[-1]["segment"] == "low"
