import numpy as np
import pytest

from options_vol_lab.pricers.black_scholes import black_scholes_price
from options_vol_lab.heston.pricer import heston_price
from options_vol_lab.heston.simulate import simulate_heston_terminal, mc_price_from_terminal


def test_heston_degenerates_to_black_scholes_when_vol_of_vol_vanishes():
    # With sigma_v -> 0 and rho = 0, variance stays essentially constant at v0,
    # so Heston should reduce to Black-Scholes with sigma = sqrt(v0).
    spot, strike, rate, ttm = 100.0, 100.0, 0.05, 1.0
    v0 = 0.04
    bs = black_scholes_price(spot, strike, rate, np.sqrt(v0), ttm, "call")
    heston = heston_price(spot, strike, rate, ttm, kappa=2.0, theta=v0, sigma_v=1e-4,
                           rho=0.0, v0=v0, option_type="call")
    assert heston == pytest.approx(bs, abs=1e-3)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_heston_put_call_parity(option_type):
    spot, strike, rate, ttm = 100.0, 95.0, 0.03, 0.75
    params = dict(kappa=1.5, theta=0.05, sigma_v=0.4, rho=-0.6, v0=0.06)
    call = heston_price(spot, strike, rate, ttm, option_type="call", **params)
    put = heston_price(spot, strike, rate, ttm, option_type="put", **params)
    assert call - put == pytest.approx(spot - strike * np.exp(-rate * ttm), abs=1e-6)


def test_heston_mc_simulation_matches_semi_closed_form():
    spot, strike, rate, ttm = 100.0, 100.0, 0.03, 1.0
    params = dict(kappa=2.0, theta=0.05, sigma_v=0.4, rho=-0.6, v0=0.05)
    analytic = heston_price(spot, strike, rate, ttm, option_type="call", **params)

    terminal = simulate_heston_terminal(spot, rate, ttm, n_steps=200, n_paths=200_000,
                                         seed=11, **params)
    mc_price, se = mc_price_from_terminal(terminal, strike, rate, ttm, "call")

    assert abs(mc_price - analytic) < 5 * se
    assert abs(mc_price - analytic) < 0.15
