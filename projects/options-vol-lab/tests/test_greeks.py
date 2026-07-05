import pytest

from options_vol_lab.greeks.analytic import analytic_greeks
from options_vol_lab.greeks.finite_diff import finite_difference_greeks
from options_vol_lab.pricers.black_scholes import black_scholes_price


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("spot,strike,rate,vol,ttm,div", [
    (100.0, 100.0, 0.05, 0.20, 1.0, 0.0),
    (80.0, 100.0, 0.03, 0.35, 0.25, 0.02),
    (120.0, 100.0, 0.01, 0.15, 2.0, 0.0),
])
def test_analytic_matches_finite_difference(spot, strike, rate, vol, ttm, div, option_type):
    analytic = analytic_greeks(spot, strike, rate, vol, ttm, option_type, div)
    fd = finite_difference_greeks(black_scholes_price, spot, strike, rate, vol, ttm, option_type, div)

    assert analytic.delta == pytest.approx(fd.delta, abs=1e-4)
    assert analytic.gamma == pytest.approx(fd.gamma, abs=1e-3)
    assert analytic.vega == pytest.approx(fd.vega, abs=1e-3)
    assert analytic.theta == pytest.approx(fd.theta, abs=1e-2)
    assert analytic.rho == pytest.approx(fd.rho, abs=1e-3)


def test_call_delta_between_zero_and_one():
    g = analytic_greeks(100, 100, 0.05, 0.2, 1.0, "call")
    assert 0.0 < g.delta < 1.0


def test_put_delta_between_minus_one_and_zero():
    g = analytic_greeks(100, 100, 0.05, 0.2, 1.0, "put")
    assert -1.0 < g.delta < 0.0


def test_gamma_and_vega_identical_for_call_and_put():
    # Gamma and vega are the same for calls and puts at identical parameters
    # (only delta, theta, rho differ by exercise style).
    call = analytic_greeks(100, 105, 0.04, 0.25, 0.5, "call")
    put = analytic_greeks(100, 105, 0.04, 0.25, 0.5, "put")
    assert call.gamma == pytest.approx(put.gamma, abs=1e-10)
    assert call.vega == pytest.approx(put.vega, abs=1e-10)
