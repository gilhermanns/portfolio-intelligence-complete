import numpy as np

from credit_risk_model.data import FEATURE_COLUMNS, apply_macro_shock, generate_borrowers


def test_default_rate_within_tolerance():
    df = generate_borrowers(n=30_000, seed=1, target_default_rate=0.10)
    assert abs(df["default"].mean() - 0.10) < 0.01


def test_default_rate_calibrates_to_different_targets():
    for target in (0.05, 0.15, 0.25):
        df = generate_borrowers(n=20_000, seed=2, target_default_rate=target)
        assert abs(df["default"].mean() - target) < 0.015


def test_schema_and_ranges():
    df = generate_borrowers(n=2_000, seed=3)
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    assert (df["income"] > 0).all()
    assert df["utilization"].between(0, 1).all()
    assert df["dti"].between(0, 1).all()
    assert (df["delinquencies_2y"] >= 0).all()
    assert set(df["default"].unique()) <= {0, 1}


def test_reproducible_with_same_seed():
    df1 = generate_borrowers(n=1_000, seed=7)
    df2 = generate_borrowers(n=1_000, seed=7)
    assert df1["default"].equals(df2["default"])
    assert np.allclose(df1["income"], df2["income"])


def test_riskier_segments_have_higher_true_pd():
    df = generate_borrowers(n=30_000, seed=4)
    by_purpose = df.groupby("loan_purpose")["true_pd"].mean()
    assert by_purpose["small_business"] > by_purpose["home_improvement"]
    by_employment = df.groupby("employment_status")["true_pd"].mean()
    assert by_employment["unemployed"] > by_employment["employed"]


def test_apply_macro_shock_shifts_unemployment_and_raises_true_pd():
    df = generate_borrowers(n=5_000, seed=5)
    shocked = apply_macro_shock(df, unemployment_delta=5.0)
    assert np.allclose(shocked["unemployment_rate"] - df["unemployment_rate"], 5.0)
    # feature columns other than the shocked one are untouched
    assert shocked["income"].equals(df["income"])
