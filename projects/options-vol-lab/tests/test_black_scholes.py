import numpy as np
import pytest

from options_vol_lab.pricers.black_scholes import black_scholes_price


def test_known_textbook_value():
    # Hull, "Options, Futures, and Other Derivatives": S=42, K=40, r=0.10,
    # sigma=0.20, T=0.5 -> call ~= 4.76, put ~= 0.81 (Hull's own example uses
    # continuous compounding and gives call price 4.76.)
    call = black_scholes_price(42, 40, 0.10, 0.20, 0.5, "call")
    assert call == pytest.approx(4.7594, abs=1e-3)


def test_put_call_parity_no_dividend():
    spot, strike, rate, vol, ttm = 105.0, 100.0, 0.03, 0.22, 0.75
    call = black_scholes_price(spot, strike, rate, vol, ttm, "call")
    put = black_scholes_price(spot, strike, rate, vol, ttm, "put")
    lhs = call - put
    rhs = spot - strike * np.exp(-rate * ttm)
    assert lhs == pytest.approx(rhs, abs=1e-8)


def test_put_call_parity_with_dividend():
    spot, strike, rate, vol, ttm, div = 60.0, 65.0, 0.02, 0.30, 1.25, 0.015
    call = black_scholes_price(spot, strike, rate, vol, ttm, "call", div)
    put = black_scholes_price(spot, strike, rate, vol, ttm, "put", div)
    lhs = call - put
    rhs = spot * np.exp(-div * ttm) - strike * np.exp(-rate * ttm)
    assert lhs == pytest.approx(rhs, abs=1e-8)


def test_deep_itm_call_converges_to_intrinsic_forward():
    price = black_scholes_price(spot=1000, strike=1, rate=0.01, vol=0.2, ttm=1.0, option_type="call")
    forward_value = 1000 - 1 * np.exp(-0.01)
    assert price == pytest.approx(forward_value, rel=1e-6)


def test_deep_otm_call_near_zero():
    price = black_scholes_price(spot=10, strike=1000, rate=0.01, vol=0.2, ttm=1.0, option_type="call")
    assert price == pytest.approx(0.0, abs=1e-6)


def test_invalid_option_type_raises():
    with pytest.raises(ValueError):
        black_scholes_price(100, 100, 0.05, 0.2, 1.0, option_type="straddle")


@pytest.mark.parametrize("strike", [0.01, 1.0, 1_000_000.0])
def test_put_call_parity_at_extreme_strikes(strike):
    # Parity is a model-free no-arbitrage identity, so it must hold exactly
    # (up to floating point) however far the strike sits from the spot --
    # near-worthless low strikes and effectively unreachable high strikes
    # alike, not just the well-behaved near-the-money case above.
    spot, rate, vol, ttm = 100.0, 0.03, 0.20, 1.0
    call = black_scholes_price(spot, strike, rate, vol, ttm, "call")
    put = black_scholes_price(spot, strike, rate, vol, ttm, "put")
    lhs = call - put
    rhs = spot - strike * np.exp(-rate * ttm)
    assert lhs == pytest.approx(rhs, abs=1e-6)


def test_zero_ttm_raises():
    with pytest.raises(ValueError):
        black_scholes_price(100, 100, 0.05, 0.2, 0.0, option_type="call")


def test_zero_vol_raises():
    with pytest.raises(ValueError):
        black_scholes_price(100, 100, 0.05, 0.0, 1.0, option_type="call")
