import numpy as np

from credit_risk_model.calibration import fit_calibrator
from credit_risk_model.data import FEATURE_COLUMNS, TARGET_COLUMN, generate_borrowers
from credit_risk_model.models import build_logistic_pipeline
from credit_risk_model.pipeline import train_all


def test_split_indices_partition_the_full_dataset_with_no_overlap():
    artifacts = train_all(n=5_000, seed=17)
    train_idx, calib_idx, test_idx = artifacts.train_idx, artifacts.calib_idx, artifacts.test_idx

    assert len(set(train_idx) & set(calib_idx)) == 0
    assert len(set(train_idx) & set(test_idx)) == 0
    assert len(set(calib_idx) & set(test_idx)) == 0

    all_idx = np.concatenate([train_idx, calib_idx, test_idx])
    assert len(all_idx) == len(artifacts.df)
    assert set(all_idx) == set(artifacts.df.index)


def test_split_fractions_match_requested_60_20_20():
    artifacts = train_all(n=10_000, seed=18, train_frac=0.6, calib_frac=0.2)
    n = len(artifacts.df)
    assert abs(len(artifacts.train_idx) / n - 0.6) < 0.01
    assert abs(len(artifacts.calib_idx) / n - 0.2) < 0.01
    assert abs(len(artifacts.test_idx) / n - 0.2) < 0.01


def test_split_is_stratified_on_default_rate():
    artifacts = train_all(n=10_000, seed=19)
    df = artifacts.df
    overall_rate = df[TARGET_COLUMN].mean()
    for idx in (artifacts.train_idx, artifacts.calib_idx, artifacts.test_idx):
        split_rate = df.loc[idx, TARGET_COLUMN].mean()
        assert abs(split_rate - overall_rate) < 0.02


def test_calibrator_fitting_does_not_mutate_base_pipeline_coefficients():
    """Calibration must be a read-only wrapper: fitting ``CalibratedClassifierCV``
    on the calibration split should never change the already-fitted logistic
    pipeline's learned coefficients. If it did, the "calibration never
    re-touches the training data" claim in the README would be false -- the
    base model would have quietly re-fit against the calibration split.
    """
    df = generate_borrowers(n=5_000, seed=20)
    pipeline = build_logistic_pipeline()
    pipeline.fit(df[FEATURE_COLUMNS], df[TARGET_COLUMN])
    coefs_before = pipeline.named_steps["clf"].coef_.copy()
    intercept_before = pipeline.named_steps["clf"].intercept_.copy()

    # Calibrate against a disjoint slice; the base pipeline object is shared,
    # not re-fit.
    calib_slice = df.iloc[:1000]
    fit_calibrator(pipeline, calib_slice[FEATURE_COLUMNS], calib_slice[TARGET_COLUMN], method="isotonic")

    assert np.array_equal(coefs_before, pipeline.named_steps["clf"].coef_)
    assert np.array_equal(intercept_before, pipeline.named_steps["clf"].intercept_)
