import pytest

from portfolio_optimizer.constraints import Constraints


def test_max_weight_out_of_range_rejected():
    with pytest.raises(ValueError):
        Constraints(max_weight=1.5).validate(10)
    with pytest.raises(ValueError):
        Constraints(max_weight=0.0).validate(10)


def test_infeasible_max_weight_rejected():
    with pytest.raises(ValueError):
        Constraints(max_weight=0.05).validate(10)  # 0.05 * 10 == 0.5 < 1


def test_feasible_constraints_pass_validation():
    Constraints(max_weight=0.25).validate(13)
