import numpy as np
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split

from credit_risk_model.calibration import fit_calibrator
from credit_risk_model.data import FEATURE_COLUMNS, TARGET_COLUMN, generate_borrowers
from credit_risk_model.models import build_logistic_pipeline


def _three_way_split(seed=21):
    df = generate_borrowers(n=20_000, seed=seed)
    train_df, rest = train_test_split(df, train_size=0.6, random_state=seed, stratify=df[TARGET_COLUMN])
    calib_df, test_df = train_test_split(rest, train_size=0.5, random_state=seed, stratify=rest[TARGET_COLUMN])
    return train_df, calib_df, test_df


def test_sigmoid_calibration_improves_brier_on_held_out_test_set():
    train_df, calib_df, test_df = _three_way_split()
    pipe = build_logistic_pipeline()
    pipe.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])

    calibrator = fit_calibrator(pipe, calib_df[FEATURE_COLUMNS], calib_df[TARGET_COLUMN], method="sigmoid")

    y_test = test_df[TARGET_COLUMN].to_numpy()
    raw_scores = pipe.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    calibrated_scores = calibrator.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]

    raw_brier = brier_score_loss(y_test, raw_scores)
    calibrated_brier = brier_score_loss(y_test, calibrated_scores)
    assert calibrated_brier < raw_brier


def test_isotonic_calibration_improves_brier_on_held_out_test_set():
    train_df, calib_df, test_df = _three_way_split(seed=22)
    pipe = build_logistic_pipeline()
    pipe.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])

    calibrator = fit_calibrator(pipe, calib_df[FEATURE_COLUMNS], calib_df[TARGET_COLUMN], method="isotonic")

    y_test = test_df[TARGET_COLUMN].to_numpy()
    raw_scores = pipe.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    calibrated_scores = calibrator.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]

    raw_brier = brier_score_loss(y_test, raw_scores)
    calibrated_brier = brier_score_loss(y_test, calibrated_scores)
    assert calibrated_brier < raw_brier


def test_calibrated_mean_prediction_tracks_observed_rate():
    train_df, calib_df, test_df = _three_way_split(seed=23)
    pipe = build_logistic_pipeline()
    pipe.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])
    calibrator = fit_calibrator(pipe, calib_df[FEATURE_COLUMNS], calib_df[TARGET_COLUMN], method="isotonic")

    calibrated_scores = calibrator.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    observed_rate = test_df[TARGET_COLUMN].mean()
    assert abs(calibrated_scores.mean() - observed_rate) < 0.02
