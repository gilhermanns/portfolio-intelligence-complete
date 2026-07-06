import pytest

from options_vol_lab.pricers.black_scholes import black_scholes_price
from options_vol_lab.pricers.binomial import binomial_price


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_european_binomial_converges_to_black_scholes(option_type):
    spot, strike, rate, vol, ttm = 100.0, 105.0, 0.04, 0.25, 1.0
    bs = black_scholes_price(spot, strike, rate, vol, ttm, option_type)

    errors = []
    for steps in (50, 200, 800, 3200):
        price = binomial_price(spot, strike, rate, vol, ttm, option_type, steps=steps)
        errors.append(abs(price - bs))

    # Error should shrink as steps grow, and the finest tree should be tight.
    assert errors[-1] < errors[0]
    assert errors[-1] < 1e-3


def test_american_call_no_dividend_equals_european():
    # With no dividends, early exercise of an American call is never optimal,
    # so American == European.
    spot, strike, rate, vol, ttm = 100.0, 90.0, 0.05, 0.2, 1.0
    euro = binomial_price(spot, strike, rate, vol, ttm, "call", steps=500, american=False)
    amer = binomial_price(spot, strike, rate, vol, ttm, "call", steps=500, american=True)
    assert amer == pytest.approx(euro, abs=1e-6)


def test_american_put_premium_over_european():
    # Early exercise can be optimal for puts, so American >= European strictly
    # for a deep ITM put with a decent rate.
    spot, strike, rate, vol, ttm = 80.0, 100.0, 0.06, 0.2, 1.0
    euro = binomial_price(spot, strike, rate, vol, ttm, "put", steps=500, american=False)
    amer = binomial_price(spot, strike, rate, vol, ttm, "put", steps=500, american=True)
    assert amer >= euro
    assert amer > euro + 1e-3


def test_invalid_risk_neutral_probability_raises():
    with pytest.raises(ValueError):
        # One giant step with a very high rate relative to vol pushes the
        # implied risk-neutral probability outside (0, 1).
        binomial_price(100, 100, 1.0, 0.01, 1.0, steps=1)


def test_zero_ttm_raises():
    with pytest.raises(ValueError):
        binomial_price(100, 100, 0.05, 0.2, 0.0, steps=10)


def test_zero_vol_raises():
    with pytest.raises(ValueError):
        binomial_price(100, 100, 0.05, 0.0, 1.0, steps=10)


def test_american_call_early_exercise_premium_with_dividend():
    # Unlike the no-dividend case, a high continuous dividend yield makes
    # early exercise of an American call rational (you give up the dividend
    # by holding the option instead of the stock), so American should trade
    # strictly above European once the yield is large enough relative to
    # the rate.
    spot, strike, rate, vol, ttm, div = 100.0, 90.0, 0.03, 0.2, 1.0, 0.08
    euro = binomial_price(spot, strike, rate, vol, ttm, "call", div=div, steps=500, american=False)
    amer = binomial_price(spot, strike, rate, vol, ttm, "call", div=div, steps=500, american=True)
    assert amer >= euro
    assert amer > euro + 1e-3
