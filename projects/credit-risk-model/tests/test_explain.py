import numpy as np
from sklearn.model_selection import train_test_split

from credit_risk_model.data import FEATURE_COLUMNS, TARGET_COLUMN, generate_borrowers
from credit_risk_model.explain import build_linear_explainer, compute_shap_values, explain_instance, global_importance
from credit_risk_model.features import feature_names_out
from credit_risk_model.models import build_logistic_pipeline


def _fitted_pipeline_and_split(seed=30):
    df = generate_borrowers(n=6_000, seed=seed)
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=seed, stratify=df[TARGET_COLUMN])
    pipeline = build_logistic_pipeline()
    pipeline.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])
    return pipeline, train_df, test_df


def test_shap_values_shape_matches_transformed_feature_matrix():
    pipeline, train_df, test_df = _fitted_pipeline_and_split()
    background = train_df[FEATURE_COLUMNS].sample(n=200, random_state=1)
    explainer, background_transformed = build_linear_explainer(pipeline, background)

    shap_values = compute_shap_values(pipeline, explainer, test_df[FEATURE_COLUMNS])
    feature_names = feature_names_out(pipeline.named_steps["preprocess"])

    assert shap_values.shape == (len(test_df), len(feature_names))
    assert background_transformed.shape[1] == len(feature_names)


def test_shap_values_reconstruct_the_models_raw_logit():
    """SHAP's additivity guarantee: base_value + sum(shap values for a row)
    must equal the model's raw logit for that row. This is the property that
    makes per-applicant explanations trustworthy rather than decorative."""
    pipeline, train_df, test_df = _fitted_pipeline_and_split(seed=31)
    background = train_df[FEATURE_COLUMNS].sample(n=300, random_state=2)
    explainer, _ = build_linear_explainer(pipeline, background)

    sample = test_df[FEATURE_COLUMNS].iloc[:25]
    shap_values = compute_shap_values(pipeline, explainer, sample)

    clf = pipeline.named_steps["clf"]
    preprocessor = pipeline.named_steps["preprocess"]
    X_transformed = np.asarray(preprocessor.transform(sample))
    true_logit = X_transformed @ clf.coef_[0] + clf.intercept_[0]

    reconstructed = float(explainer.expected_value) + shap_values.sum(axis=1)
    assert np.allclose(reconstructed, true_logit, atol=1e-8)


def test_global_importance_ranks_known_strong_drivers_above_weak_ones():
    """The DGP (data.py) makes utilization and DTI strong, direct drivers of
    default risk and credit_history_years a weaker one; a correctly wired
    SHAP pipeline should recover that ordering on average."""
    pipeline, train_df, test_df = _fitted_pipeline_and_split(seed=32)
    background = train_df[FEATURE_COLUMNS].sample(n=300, random_state=3)
    explainer, _ = build_linear_explainer(pipeline, background)
    shap_values = compute_shap_values(pipeline, explainer, test_df[FEATURE_COLUMNS])
    feature_names = feature_names_out(pipeline.named_steps["preprocess"])

    importance = global_importance(shap_values, feature_names).set_index("feature")["mean_abs_shap"]
    assert importance["num__utilization"] > importance["num__credit_history_years"]
    assert importance["num__dti"] > importance["num__credit_history_years"]


def test_explain_instance_returns_base_value_and_top_k_drivers_sorted_by_magnitude():
    shap_row = np.array([0.1, -0.9, 0.05, 0.3, -0.2])
    feature_names = ["a", "b", "c", "d", "e"]
    result = explain_instance(shap_row, feature_names, base_value=-0.5, top_k=3)

    assert result["base_value"] == -0.5
    assert [d["feature"] for d in result["drivers"]] == ["b", "d", "e"]
    assert result["drivers"][0]["direction"] == "decreases risk"
    assert result["drivers"][1]["direction"] == "increases risk"
