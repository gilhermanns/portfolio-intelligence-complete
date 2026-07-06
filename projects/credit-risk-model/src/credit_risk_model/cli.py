"""Underwriting decision CLI: score a single applicant end to end.

Stands in for "a web app for underwriting decisions" per the project scope.
Trains the logistic PD pipeline and its calibrator in-process against the
fixed-seed synthetic dataset (sub-second) rather than loading a serialized
model file, so the tool is fully reproducible from source with no binary
artifacts to ship or go stale.
"""

from __future__ import annotations

import argparse

import pandas as pd

from credit_risk_model.data import EMPLOYMENT_STATUSES, FEATURE_COLUMNS, LOAN_PURPOSES
from credit_risk_model.explain import build_linear_explainer, compute_shap_values, explain_instance
from credit_risk_model.features import feature_names_out
from credit_risk_model.pipeline import train_all


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="credit-risk",
        description="Score a loan applicant: PD, calibrated PD, and an approve/refer/decline decision.",
    )
    parser.add_argument("--income", type=float, required=True, help="Annual income in dollars")
    parser.add_argument("--dti", type=float, required=True, help="Debt-to-income ratio, e.g. 0.35")
    parser.add_argument("--utilization", type=float, required=True, help="Credit utilization, 0-1")
    parser.add_argument("--credit-history-years", type=float, required=True)
    parser.add_argument("--delinquencies-2y", type=int, required=True)
    parser.add_argument("--unemployment-rate", type=float, required=True, help="Prevailing macro rate, percent")
    parser.add_argument("--loan-purpose", choices=LOAN_PURPOSES, required=True)
    parser.add_argument("--employment-status", choices=EMPLOYMENT_STATUSES, required=True)
    parser.add_argument(
        "--calibration", choices=["sigmoid", "isotonic"], default="isotonic", help="Calibration method to report"
    )
    parser.add_argument("--approve-threshold", type=float, default=0.07, help="Calibrated PD below this: approve")
    parser.add_argument("--decline-threshold", type=float, default=0.20, help="Calibrated PD at/above this: decline")
    parser.add_argument("--seed", type=int, default=42, help="Training data/model seed, for reproducibility")
    parser.add_argument("--n", type=int, default=20_000, help="Synthetic portfolio size used to train the model")
    return parser


def _decide(calibrated_pd: float, approve_threshold: float, decline_threshold: float) -> str:
    if calibrated_pd < approve_threshold:
        return "approve"
    if calibrated_pd >= decline_threshold:
        return "decline"
    return "refer"


def score_applicant(args: argparse.Namespace) -> dict:
    artifacts = train_all(n=args.n, seed=args.seed)
    pipeline = artifacts.logistic_pipeline
    calibrator = artifacts.calibrator_isotonic if args.calibration == "isotonic" else artifacts.calibrator_sigmoid

    applicant = pd.DataFrame(
        [
            {
                "income": args.income,
                "dti": args.dti,
                "utilization": args.utilization,
                "credit_history_years": args.credit_history_years,
                "delinquencies_2y": args.delinquencies_2y,
                "unemployment_rate": args.unemployment_rate,
                "loan_purpose": args.loan_purpose,
                "employment_status": args.employment_status,
            }
        ]
    )[FEATURE_COLUMNS]

    raw_pd = float(pipeline.predict_proba(applicant)[:, 1][0])
    calibrated_pd = float(calibrator.predict_proba(applicant)[:, 1][0])
    decision = _decide(calibrated_pd, args.approve_threshold, args.decline_threshold)

    train_df = artifacts.df.loc[artifacts.train_idx]
    background = train_df[FEATURE_COLUMNS].sample(n=min(200, len(train_df)), random_state=args.seed)
    explainer, _ = build_linear_explainer(pipeline, background)
    shap_row = compute_shap_values(pipeline, explainer, applicant)[0]
    feature_names = feature_names_out(pipeline.named_steps["preprocess"])
    explanation = explain_instance(shap_row, feature_names, base_value=float(explainer.expected_value), top_k=5)

    return {
        "raw_pd": raw_pd,
        "calibrated_pd": calibrated_pd,
        "calibration_method": args.calibration,
        "decision": decision,
        "approve_threshold": args.approve_threshold,
        "decline_threshold": args.decline_threshold,
        "base_logit": explanation["base_value"],
        "top_drivers": explanation["drivers"],
    }


def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    result = score_applicant(args)

    print("Credit Risk Underwriting Decision")
    print("-" * 40)
    print(f"Raw model PD:        {result['raw_pd']:.4f}")
    print(f"Calibrated PD ({result['calibration_method']:>8s}): {result['calibrated_pd']:.4f}")
    print(f"Decision cutoffs:    approve < {result['approve_threshold']:.2f} <= refer < {result['decline_threshold']:.2f} <= decline")
    print(f"Decision:            {result['decision'].upper()}")
    print()
    print(f"Top drivers (SHAP, logit scale, vs. baseline {result['base_logit']:+.4f}):")
    for d in result["top_drivers"]:
        print(f"  {d['feature']:<35s} {d['shap_value']:+.4f}  ({d['direction']})")


if __name__ == "__main__":
    main()
