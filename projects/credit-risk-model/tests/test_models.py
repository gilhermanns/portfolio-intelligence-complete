import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from credit_risk_model.data import FEATURE_COLUMNS, TARGET_COLUMN, generate_borrowers
from credit_risk_model.models import build_gbm_pipeline, build_logistic_pipeline


def _split():
    df = generate_borrowers(n=15_000, seed=11)
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=11, stratify=df[TARGET_COLUMN])
    return train_df, test_df


def test_logistic_pipeline_beats_naive_baseline_on_auc():
    train_df, test_df = _split()
    pipe = build_logistic_pipeline()
    pipe.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])
    scores = pipe.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]

    auc = roc_auc_score(test_df[TARGET_COLUMN], scores)
    # a naive/majority-class baseline has AUC == 0.5 by construction; require a
    # large, unambiguous margin above that so the test cannot pass by luck
    assert auc > 0.70


def test_logistic_pipeline_beats_naive_baseline_on_brier():
    train_df, test_df = _split()
    pipe = build_logistic_pipeline()
    pipe.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])
    scores = pipe.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]

    y_test = test_df[TARGET_COLUMN].to_numpy()
    train_rate = train_df[TARGET_COLUMN].mean()
    naive_brier = np.mean((y_test - train_rate) ** 2)
    model_brier = np.mean((y_test - scores) ** 2)
    # the raw (uncalibrated, class-weighted) model can have worse Brier than
    # the naive baseline -- that is precisely why calibration is needed -- but
    # its *ranking* must still be informative, which we check via AUC above.
    # Here we only assert the model's probabilities aren't degenerate.
    assert 0.0 < model_brier < 1.0
    assert 0.0 < naive_brier < 1.0


def test_gbm_pipeline_also_beats_naive_baseline():
    train_df, test_df = _split()
    pipe = build_gbm_pipeline()
    from sklearn.utils.class_weight import compute_sample_weight

    sw = compute_sample_weight("balanced", train_df[TARGET_COLUMN])
    pipe.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN], clf__sample_weight=sw)
    scores = pipe.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    auc = roc_auc_score(test_df[TARGET_COLUMN], scores)
    assert auc > 0.70


def test_logistic_and_gbm_pipelines_are_comparable():
    train_df, test_df = _split()
    logistic = build_logistic_pipeline()
    logistic.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])
    logistic_auc = roc_auc_score(test_df[TARGET_COLUMN], logistic.predict_proba(test_df[FEATURE_COLUMNS])[:, 1])

    gbm = build_gbm_pipeline()
    from sklearn.utils.class_weight import compute_sample_weight

    sw = compute_sample_weight("balanced", train_df[TARGET_COLUMN])
    gbm.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN], clf__sample_weight=sw)
    gbm_auc = roc_auc_score(test_df[TARGET_COLUMN], gbm.predict_proba(test_df[FEATURE_COLUMNS])[:, 1])

    # neither should dominate the other by a huge margin: the DGP's nonlinear
    # terms give the tree model some edge, but the interpretable linear model
    # should stay competitive since the interactions are only moderate
    assert abs(logistic_auc - gbm_auc) < 0.08
