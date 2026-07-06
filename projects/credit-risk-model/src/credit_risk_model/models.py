"""PD model definitions: logistic regression (primary) and gradient-boosted trees (baseline)."""

from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from credit_risk_model.features import build_preprocessor


def build_logistic_pipeline(C: float = 1.0) -> Pipeline:
    """Scaled logistic regression with balanced class weights for the ~10% minority default class."""
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "clf",
                LogisticRegression(
                    C=C,
                    class_weight="balanced",
                    max_iter=2000,
                    solver="lbfgs",
                ),
            ),
        ]
    )


def build_gbm_pipeline(random_state: int = 42) -> Pipeline:
    """HistGradientBoostingClassifier baseline: captures nonlinearities/interactions the DGP has."""
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "clf",
                HistGradientBoostingClassifier(
                    max_depth=6,
                    learning_rate=0.06,
                    max_iter=300,
                    l2_regularization=1.0,
                    random_state=random_state,
                ),
            ),
        ]
    )
