import pandas as pd

from portfolio_optimizer import data as data_mod


def test_bundled_cache_loads_and_is_gap_free(tickers):
    df, used_live = data_mod.load_prices(tickers, use_cache_only=True)
    assert used_live is False
    assert not df.isna().any().any()
    assert list(df.columns) == tickers
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing


def test_date_filtering(tickers):
    df, _ = data_mod.load_prices(tickers, start="2020-01-01", end="2020-12-31", use_cache_only=True)
    assert df.index.min() >= pd.Timestamp("2020-01-01")
    assert df.index.max() <= pd.Timestamp("2020-12-31")
    assert len(df) > 200  # roughly a trading year


def test_unknown_ticker_raises(tickers):
    import pytest

    with pytest.raises(ValueError):
        data_mod.load_prices(tickers + ["NOTAREALTICKER"], use_cache_only=True)


def test_live_fetch_failure_falls_back_to_cache(tickers, monkeypatch):
    monkeypatch.setattr(data_mod, "_fetch_one_from_stooq", lambda ticker: None)
    df, used_live = data_mod.load_prices(tickers, use_cache_only=False)
    assert used_live is False
    assert not df.isna().any().any()
