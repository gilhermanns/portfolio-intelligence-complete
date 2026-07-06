# Quant Finance Projects

Seven self-contained Python projects, each with its own tests, README, and
generated results. Every number in each README comes from an actual run of
the code — nothing is hand-typed or estimated. Every project's install
instructions are copy-pasteable and its test suite passes on a clean venv.

| Project | What it does |
|---|---|
| [portfolio-optimizer](portfolio-optimizer/) | Mean-variance, minimum-variance, risk-parity, and Black-Litterman optimization with position/sector caps and turnover costs, backtested against equal-weight on 13 real tickers. |
| [walkforward-backtester](walkforward-backtester/) | MA-crossover, RSI mean-reversion, and Donchian breakout strategies with realistic slippage/commissions, validated with a rolling walk-forward train/validation/test split. |
| [orderbook-microstructure-sim](orderbook-microstructure-sim/) | An event-driven limit order book with liquidity-provider, momentum, and noise-trader agents, used to study spread dynamics, adverse selection, and execution cost. |
| [portfolio-risk-dashboard](portfolio-risk-dashboard/) | Historical, parametric, and Monte Carlo VaR/ES compared side by side, plus factor attribution, correlation-regime shifts, and historical crisis stress tests. |
| [options-vol-lab](options-vol-lab/) | Black-Scholes, binomial, and Monte Carlo option pricers cross-validated against each other, analytic and numerical Greeks, and Heston stochastic-volatility calibration. |
| [sentiment-market-signals](sentiment-market-signals/) | An NLP pipeline that scores financial headlines for sentiment and rigorously tests — with no-lookahead lag regressions and an event study — whether it actually predicts returns. |
| [credit-risk-model](credit-risk-model/) | A probability-of-default scorecard with calibration, SHAP explainability, segment analysis, and a Monte Carlo expected-loss simulation under a macro stress scenario. |

Each project lives in its own directory and is independently installable
(`pip install -e .` inside that directory) — they don't depend on each other
or on the dashboard app in the repo root.
