"""Command-line entry point: price a single option and print pricer comparison + Greeks."""
from __future__ import annotations

import argparse
import sys

from options_vol_lab.pricers.black_scholes import black_scholes_price
from options_vol_lab.pricers.binomial import binomial_price
from options_vol_lab.pricers.monte_carlo import monte_carlo_price
from options_vol_lab.greeks.analytic import analytic_greeks
from options_vol_lab.greeks.finite_diff import finite_difference_greeks


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ovl-price",
        description="Price a European/American option and report cross-model checks and Greeks.",
    )
    p.add_argument("--spot", type=float, required=True, help="Spot price")
    p.add_argument("--strike", type=float, required=True, help="Strike price")
    p.add_argument("--rate", type=float, required=True, help="Risk-free rate (annualized, decimal)")
    p.add_argument("--vol", type=float, required=True, help="Volatility (annualized, decimal)")
    p.add_argument("--ttm", type=float, required=True, help="Time to maturity in years")
    p.add_argument("--type", choices=["call", "put"], default="call", dest="option_type")
    p.add_argument("--div", type=float, default=0.0, help="Continuous dividend yield")
    p.add_argument("--american", action="store_true", help="Price as American (binomial only)")
    p.add_argument("--steps", type=int, default=500, help="Binomial tree steps")
    p.add_argument("--paths", type=int, default=200_000, help="Monte Carlo paths")
    p.add_argument("--seed", type=int, default=None, help="Monte Carlo RNG seed")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)

    try:
        bs = black_scholes_price(args.spot, args.strike, args.rate, args.vol, args.ttm,
                                  args.option_type, args.div)
        binom = binomial_price(args.spot, args.strike, args.rate, args.vol, args.ttm,
                                args.option_type, args.div, steps=args.steps, american=args.american)
        mc = monte_carlo_price(args.spot, args.strike, args.rate, args.vol, args.ttm,
                                args.option_type, args.div, n_paths=args.paths, seed=args.seed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    greeks_a = analytic_greeks(args.spot, args.strike, args.rate, args.vol, args.ttm,
                               args.option_type, args.div)
    greeks_fd = finite_difference_greeks(black_scholes_price, args.spot, args.strike, args.rate,
                                          args.vol, args.ttm, args.option_type, args.div)

    print(f"Option: {args.option_type}  S={args.spot}  K={args.strike}  r={args.rate}  "
          f"sigma={args.vol}  T={args.ttm}  q={args.div}  american={args.american}")
    print("-" * 72)
    print(f"{'Black-Scholes:':<24}{bs:.6f}")
    print(f"{'Binomial (CRR):':<24}{binom:.6f}  (steps={args.steps})")
    print(f"{'Monte Carlo:':<24}{mc.price:.6f}  +/- {mc.std_error:.6f}  (paths={args.paths})")
    print("-" * 72)
    print(f"{'Greek':<10}{'Analytic':>14}{'Finite Diff':>16}")
    for name in ("delta", "gamma", "vega", "theta", "rho"):
        print(f"{name:<10}{getattr(greeks_a, name):>14.6f}{getattr(greeks_fd, name):>16.6f}")


if __name__ == "__main__":
    main()
