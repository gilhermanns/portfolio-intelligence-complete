"""Feature preprocessing shared by all model pipelines."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from credit_risk_model.data import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """Standard-scale numeric features and one-hot encode categoricals.

    Scaling matters for logistic regression's coefficients and its L2 penalty;
    it is a no-op for the tree baseline but shared here to keep both models
    fed by the exact same feature matrix.
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CATEGORICAL_FEATURES),
        ]
    )


def feature_names_out(preprocessor: ColumnTransformer) -> list[str]:
    return list(preprocessor.get_feature_names_out())
