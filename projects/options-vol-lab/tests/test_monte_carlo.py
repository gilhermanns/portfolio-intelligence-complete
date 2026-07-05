import pytest

from options_vol_lab.pricers.black_scholes import black_scholes_price
from options_vol_lab.pricers.monte_carlo import monte_carlo_price


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_monte_carlo_converges_to_black_scholes(option_type):
    spot, strike, rate, vol, ttm = 100.0, 95.0, 0.03, 0.30, 0.75
    bs = black_scholes_price(spot, strike, rate, vol, ttm, option_type)

    result = monte_carlo_price(spot, strike, rate, vol, ttm, option_type,
                                n_paths=300_000, seed=123)
    assert abs(result.price - bs) < 5 * result.std_error
    assert abs(result.price - bs) < 0.05


def test_control_variate_reduces_standard_error():
    spot, strike, rate, vol, ttm = 100.0, 100.0, 0.02, 0.35, 1.0
    n_paths = 100_000
    plain = monte_carlo_price(spot, strike, rate, vol, ttm, "call",
                               n_paths=n_paths, antithetic=False, control_variate=False, seed=7)
    reduced = monte_carlo_price(spot, strike, rate, vol, ttm, "call",
                                 n_paths=n_paths, antithetic=True, control_variate=True, seed=7)
    assert reduced.std_error < plain.std_error


def test_monte_carlo_matches_binomial_and_bs_for_atm_option():
    from options_vol_lab.pricers.binomial import binomial_price

    spot, strike, rate, vol, ttm = 50.0, 50.0, 0.01, 0.18, 2.0
    bs = black_scholes_price(spot, strike, rate, vol, ttm, "call")
    binom = binomial_price(spot, strike, rate, vol, ttm, "call", steps=1000)
    mc = monte_carlo_price(spot, strike, rate, vol, ttm, "call", n_paths=300_000, seed=99)

    assert binom == pytest.approx(bs, abs=1e-2)
    assert mc.price == pytest.approx(bs, abs=0.05)
