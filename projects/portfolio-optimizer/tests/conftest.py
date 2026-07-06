import pytest

from portfolio_optimizer import data as data_mod
from portfolio_optimizer.moments import annualized_mean_cov, daily_returns
from portfolio_optimizer.universe import DEFAULT_SECTOR_MAP, market_weights_for, sectors_for

TEST_TICKERS = ["AAPL", "GOOG", "META", "T", "JPM", "MA", "PFE", "WMT", "SBUX", "GE", "XOM", "TLT", "GLD"]


@pytest.fixture(scope="session")
def tickers():
    return list(TEST_TICKERS)


@pytest.fixture(scope="session")
def sector_map(tickers):
    return sectors_for(tickers)


@pytest.fixture(scope="session")
def prices(tickers):
    df, _ = data_mod.load_prices(tickers, "2016-11-01", "2024-11-29", use_cache_only=True)
    return df


@pytest.fixture(scope="session")
def benchmark():
    df, _ = data_mod.load_prices(["SPY"], "2016-11-01", "2024-11-29", use_cache_only=True)
    return df["SPY"]


@pytest.fixture(scope="session")
def moments(prices, tickers):
    returns = daily_returns(prices[tickers])
    return annualized_mean_cov(returns)


@pytest.fixture(scope="session")
def mu(moments):
    return moments[0]


@pytest.fixture(scope="session")
def cov(moments):
    return moments[1]


@pytest.fixture(scope="session")
def market_weights(tickers):
    import pandas as pd

    return pd.Series(market_weights_for(tickers))


@pytest.fixture(scope="session")
def backtest_result(prices, tickers, sector_map, benchmark):
    from portfolio_optimizer.backtest import run_backtest

    return run_backtest(
        prices[tickers],
        sector_map,
        benchmark,
        window_months=48,  # longer trailing window than the README run -> fewer rebalances, faster test
        tc_bps=10.0,
        max_weight=0.25,
    )
