import pytest

from options_vol_lab.pricers.black_scholes import black_scholes_price
from options_vol_lab.implied_vol import implied_volatility


@pytest.mark.parametrize("true_vol", [0.05, 0.15, 0.25, 0.40, 0.80])
@pytest.mark.parametrize("option_type", ["call", "put"])
def test_recovers_vol_used_to_generate_price(true_vol, option_type):
    spot, strike, rate, ttm, div = 100.0, 105.0, 0.03, 0.5, 0.01
    price = black_scholes_price(spot, strike, rate, true_vol, ttm, option_type, div)
    recovered = implied_volatility(price, spot, strike, rate, ttm, option_type, div)
    assert recovered == pytest.approx(true_vol, abs=1e-6)


def test_below_intrinsic_value_raises():
    with pytest.raises(ValueError):
        implied_volatility(market_price=0.0, spot=150, strike=100, rate=0.05, ttm=1.0,
                            option_type="call")


def test_unreachable_price_raises():
    with pytest.raises(ValueError):
        implied_volatility(market_price=1000.0, spot=100, strike=100, rate=0.05, ttm=1.0,
                            option_type="call", vol_hi=1.0)
