from credit_risk_model.cli import _build_arg_parser, _decide


def test_decide_approve_below_threshold():
    assert _decide(0.03, approve_threshold=0.07, decline_threshold=0.20) == "approve"


def test_decide_refer_in_between():
    assert _decide(0.12, approve_threshold=0.07, decline_threshold=0.20) == "refer"


def test_decide_decline_at_or_above_threshold():
    assert _decide(0.20, approve_threshold=0.07, decline_threshold=0.20) == "decline"
    assert _decide(0.50, approve_threshold=0.07, decline_threshold=0.20) == "decline"


def test_decide_boundary_approve_threshold_is_exclusive():
    assert _decide(0.07, approve_threshold=0.07, decline_threshold=0.20) == "refer"


def test_arg_parser_requires_core_fields():
    parser = _build_arg_parser()
    args = parser.parse_args(
        [
            "--income",
            "60000",
            "--dti",
            "0.3",
            "--utilization",
            "0.4",
            "--credit-history-years",
            "8",
            "--delinquencies-2y",
            "0",
            "--unemployment-rate",
            "5.0",
            "--loan-purpose",
            "credit_card",
            "--employment-status",
            "employed",
        ]
    )
    assert args.income == 60000
    assert args.loan_purpose == "credit_card"
    assert args.approve_threshold == 0.07
    assert args.decline_threshold == 0.20
