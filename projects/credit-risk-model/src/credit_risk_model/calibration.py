"""Post-hoc probability calibration: Platt scaling and isotonic regression on a held-out calibration set."""

from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator


def fit_calibrator(fitted_pipeline, X_calib, y_calib, method: str = "sigmoid") -> CalibratedClassifierCV:
    """Wrap an already-fitted pipeline with a calibrator trained on a disjoint calibration split.

    ``method="sigmoid"`` is Platt scaling; ``method="isotonic"`` is nonparametric
    and more flexible but needs more calibration data to avoid overfitting.
    Fitting on data unseen by the base model avoids the double-dipping that
    would otherwise make the calibration curve look better than it truly is.
    """
    calibrator = CalibratedClassifierCV(FrozenEstimator(fitted_pipeline), method=method)
    calibrator.fit(X_calib, y_calib)
    return calibrator
