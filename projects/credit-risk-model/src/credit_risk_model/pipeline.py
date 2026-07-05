"""End-to-end training orchestration: data -> split -> fit -> calibrate.

Shared by the report-generation script and the underwriting CLI so both use
the identical train/calibration/test split and model-fitting logic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.utils.class_weight import compute_sample_weight

from credit_risk_model.calibration import fit_calibrator
from credit_risk_model.data import FEATURE_COLUMNS, TARGET_COLUMN, generate_borrowers
from credit_risk_model.models import build_gbm_pipeline, build_logistic_pipeline


@dataclass
class TrainedArtifacts:
    df: pd.DataFrame
    train_idx: np.ndarray
    calib_idx: np.ndarray
    test_idx: np.ndarray
    logistic_pipeline: Pipeline
    gbm_pipeline: Pipeline
    calibrator_sigmoid: object
    calibrator_isotonic: object


def train_all(
    n: int = 20_000,
    seed: int = 42,
    target_default_rate: float = 0.10,
    train_frac: float = 0.6,
    calib_frac: float = 0.2,
) -> TrainedArtifacts:
    df = generate_borrowers(n=n, seed=seed, target_default_rate=target_default_rate)

    train_df, temp_df = train_test_split(
        df, train_size=train_frac, random_state=seed, stratify=df[TARGET_COLUMN]
    )
    remaining_frac = 1.0 - train_frac
    calib_df, test_df = train_test_split(
        temp_df,
        train_size=calib_frac / remaining_frac,
        random_state=seed,
        stratify=temp_df[TARGET_COLUMN],
    )

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_calib, y_calib = calib_df[FEATURE_COLUMNS], calib_df[TARGET_COLUMN]

    logistic_pipeline = build_logistic_pipeline()
    logistic_pipeline.fit(X_train, y_train)

    gbm_pipeline = build_gbm_pipeline(random_state=seed)
    sample_weight = compute_sample_weight("balanced", y_train)
    gbm_pipeline.fit(X_train, y_train, clf__sample_weight=sample_weight)

    calibrator_sigmoid = fit_calibrator(logistic_pipeline, X_calib, y_calib, method="sigmoid")
    calibrator_isotonic = fit_calibrator(logistic_pipeline, X_calib, y_calib, method="isotonic")

    return TrainedArtifacts(
        df=df,
        train_idx=train_df.index.to_numpy(),
        calib_idx=calib_df.index.to_numpy(),
        test_idx=test_df.index.to_numpy(),
        logistic_pipeline=logistic_pipeline,
        gbm_pipeline=gbm_pipeline,
        calibrator_sigmoid=calibrator_sigmoid,
        calibrator_isotonic=calibrator_isotonic,
    )
