"""SHAP explainability for the logistic-regression PD model.

Uses ``shap.LinearExplainer`` directly against the fitted ``LogisticRegression``
coefficients in transformed feature space (fast, closed-form, no sampling loop),
rather than the model-agnostic ``KernelExplainer`` which would be far slower for
no accuracy benefit on a linear model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline


def build_linear_explainer(pipeline: Pipeline, X_background: pd.DataFrame) -> tuple[shap.LinearExplainer, np.ndarray]:
    preprocessor = pipeline.named_steps["preprocess"]
    clf = pipeline.named_steps["clf"]
    background_transformed = preprocessor.transform(X_background)
    background_transformed = np.asarray(background_transformed)
    explainer = shap.LinearExplainer(clf, background_transformed)
    return explainer, background_transformed


def compute_shap_values(pipeline: Pipeline, explainer: shap.LinearExplainer, X: pd.DataFrame) -> np.ndarray:
    preprocessor = pipeline.named_steps["preprocess"]
    X_transformed = np.asarray(preprocessor.transform(X))
    return explainer.shap_values(X_transformed)


def global_importance(shap_values: np.ndarray, feature_names: list[str]) -> pd.DataFrame:
    mean_abs = np.abs(shap_values).mean(axis=0)
    out = pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
    return out.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def explain_instance(
    shap_row: np.ndarray, feature_names: list[str], base_value: float, top_k: int = 5
) -> list[dict]:
    """Top contributors (by |SHAP|) for a single scored applicant, on the logit scale."""
    order = np.argsort(-np.abs(shap_row))[:top_k]
    return [
        {
            "feature": feature_names[i],
            "shap_value": float(shap_row[i]),
            "direction": "increases risk" if shap_row[i] > 0 else "decreases risk",
        }
        for i in order
    ]
