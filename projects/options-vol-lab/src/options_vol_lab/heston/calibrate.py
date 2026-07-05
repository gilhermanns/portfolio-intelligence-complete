"""Least-squares calibration of Heston parameters to a target implied-vol grid."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from options_vol_lab.greeks.analytic import analytic_greeks
from options_vol_lab.heston.pricer import heston_price
from options_vol_lab.pricers.black_scholes import black_scholes_price

PARAM_NAMES = ("kappa", "theta", "sigma_v", "rho", "v0")


@dataclass
class HestonParams:
    kappa: float
    theta: float
    sigma_v: float
    rho: float
    v0: float

    def as_array(self) -> np.ndarray:
        return np.array([self.kappa, self.theta, self.sigma_v, self.rho, self.v0])

    @classmethod
    def from_array(cls, arr) -> "HestonParams":
        return cls(*[float(x) for x in arr])


DEFAULT_BOUNDS = (
    np.array([1e-3, 1e-3, 1e-3, -0.999, 1e-3]),
    np.array([15.0, 2.0, 3.0, 0.999, 2.0]),
)


def calibrate_heston(
    strikes: np.ndarray,
    maturities: np.ndarray,
    target_ivs: np.ndarray,
    spot: float,
    rate: float,
    initial_guess: HestonParams,
    div: float = 0.0,
    bounds=DEFAULT_BOUNDS,
):
    """Calibrate (kappa, theta, sigma_v, rho, v0) to a target IV surface.

    ``target_ivs`` has shape (len(maturities), len(strikes)). Residuals are
    computed in price space and vega-weighted (Jaeckel-style) so the
    least-squares objective approximates a distance in implied-vol space
    without needing to invert the Heston price at every iteration.
    """
    strikes = np.asarray(strikes, dtype=float)
    maturities = np.asarray(maturities, dtype=float)
    target_ivs = np.asarray(target_ivs, dtype=float)

    target_prices = np.zeros((len(maturities), len(strikes)))
    vegas = np.zeros_like(target_prices)
    for i, t in enumerate(maturities):
        for k, strike in enumerate(strikes):
            iv = target_ivs[i, k]
            target_prices[i, k] = black_scholes_price(spot, strike, rate, iv, t, "call", div)
            vegas[i, k] = max(
                analytic_greeks(spot, strike, rate, iv, t, "call", div).vega, 1e-6
            )

    def residuals(x):
        params = HestonParams.from_array(x)
        res = np.zeros((len(maturities), len(strikes)))
        for i, t in enumerate(maturities):
            for k, strike in enumerate(strikes):
                model_price = heston_price(
                    spot, strike, rate, t,
                    params.kappa, params.theta, params.sigma_v, params.rho, params.v0,
                    "call", div,
                )
                res[i, k] = (model_price - target_prices[i, k]) / vegas[i, k]
        return res.ravel()

    result = least_squares(
        residuals,
        initial_guess.as_array(),
        bounds=bounds,
        method="trf",
        xtol=1e-10,
        ftol=1e-10,
        max_nfev=400,
    )
    fitted = HestonParams.from_array(result.x)
    return fitted, result
