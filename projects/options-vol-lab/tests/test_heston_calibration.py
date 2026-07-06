import numpy as np
import pytest

from options_vol_lab.heston.pricer import heston_price
from options_vol_lab.heston.calibrate import calibrate_heston, HestonParams
from options_vol_lab.implied_vol import implied_volatility


@pytest.fixture(scope="module")
def synthetic_surface():
    """Generate a noise-free target IV surface from known Heston parameters
    using the semi-closed-form pricer (validated separately in
    test_heston.py). Calibration is expected to recover these parameters
    almost exactly since there is no sampling noise -- this isolates the
    correctness of the optimizer/objective from Monte Carlo noise, which is
    exercised separately in the demo script against a Monte-Carlo-built
    surface (see reports/heston_calibration.txt)."""
    true_params = dict(kappa=2.0, theta=0.04, sigma_v=0.5, rho=-0.7, v0=0.05)
    spot, rate = 100.0, 0.03
    strikes = spot * np.array([0.85, 0.925, 1.0, 1.075, 1.15])
    maturities = np.array([0.25, 0.5, 1.0, 1.5])

    ivs = np.zeros((len(maturities), len(strikes)))
    for i, t in enumerate(maturities):
        for k, strike in enumerate(strikes):
            price = heston_price(spot, strike, rate, t, option_type="call", **true_params)
            ivs[i, k] = implied_volatility(price, spot, strike, rate, t, "call")

    return true_params, spot, rate, strikes, maturities, ivs


def test_calibration_recovers_seeded_parameters(synthetic_surface):
    true_params, spot, rate, strikes, maturities, ivs = synthetic_surface
    initial_guess = HestonParams(kappa=1.0, theta=0.06, sigma_v=0.3, rho=-0.3, v0=0.03)

    fitted, result = calibrate_heston(strikes, maturities, ivs, spot, rate, initial_guess)

    assert result.success or result.status > 0
    assert fitted.kappa == pytest.approx(true_params["kappa"], rel=0.05)
    assert fitted.theta == pytest.approx(true_params["theta"], rel=0.05)
    assert fitted.sigma_v == pytest.approx(true_params["sigma_v"], rel=0.05)
    assert fitted.rho == pytest.approx(true_params["rho"], rel=0.05)
    assert fitted.v0 == pytest.approx(true_params["v0"], rel=0.05)


def test_calibration_robust_to_poor_initial_guess(synthetic_surface):
    # A production calibration won't always get a well-informed starting
    # point. Start far from the truth and near the opposite end of a couple
    # of bounds (mean-reverting speed too fast, correlation flipped sign) and
    # confirm the optimizer still converges to the seeded parameters rather
    # than stalling in a local minimum.
    true_params, spot, rate, strikes, maturities, ivs = synthetic_surface
    poor_guess = HestonParams(kappa=10.0, theta=0.5, sigma_v=2.0, rho=0.5, v0=0.5)

    fitted, result = calibrate_heston(strikes, maturities, ivs, spot, rate, poor_guess)

    assert result.success or result.status > 0
    assert fitted.kappa == pytest.approx(true_params["kappa"], rel=0.05)
    assert fitted.theta == pytest.approx(true_params["theta"], rel=0.05)
    assert fitted.sigma_v == pytest.approx(true_params["sigma_v"], rel=0.05)
    assert fitted.rho == pytest.approx(true_params["rho"], rel=0.05)
    assert fitted.v0 == pytest.approx(true_params["v0"], rel=0.05)


def test_calibrated_model_reprices_surface_accurately(synthetic_surface):
    true_params, spot, rate, strikes, maturities, ivs = synthetic_surface
    initial_guess = HestonParams(kappa=1.0, theta=0.06, sigma_v=0.3, rho=-0.3, v0=0.03)
    fitted, _ = calibrate_heston(strikes, maturities, ivs, spot, rate, initial_guess)

    max_iv_error = 0.0
    for i, t in enumerate(maturities):
        for k, strike in enumerate(strikes):
            price = heston_price(spot, strike, rate, t, fitted.kappa, fitted.theta,
                                  fitted.sigma_v, fitted.rho, fitted.v0, "call")
            iv = implied_volatility(price, spot, strike, rate, t, "call")
            max_iv_error = max(max_iv_error, abs(iv - ivs[i, k]))

    assert max_iv_error < 0.005
