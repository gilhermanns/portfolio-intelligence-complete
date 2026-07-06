"""Price loading with a live-fetch-then-cache-fallback strategy.

Primary path: pull daily OHLC CSVs from stooq per ticker. Stooq requires no
API key, but it is a third-party service and can rate-limit, change its
verification flow, or simply be unreachable from a given network. If the
live fetch fails for any reason, callers fall back to a bundled snapshot
(``data/prices_cache.csv``) built from real historical closing prices so the
project always runs end to end without a network connection.
"""

from __future__ import annotations

import io
import logging
from importlib import resources
from pathlib import Path

import pandas as pd
import requests

from .universe import STOOQ_SYMBOLS

logger = logging.getLogger(__name__)

STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"
_REQUEST_TIMEOUT = 10


def _fetch_one_from_stooq(ticker: str) -> pd.Series | None:
    symbol = STOOQ_SYMBOLS.get(ticker, f"{ticker.lower()}.us")
    try:
        resp = requests.get(STOOQ_URL.format(symbol=symbol), timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if "Close" not in df.columns or "Date" not in df.columns or len(df) < 30:
            return None
        df["Date"] = pd.to_datetime(df["Date"])
        series = df.set_index("Date")["Close"].sort_index()
        series.name = ticker
        return series
    except Exception as exc:  # network, parsing, or rate-limit failure
        logger.warning("stooq fetch failed for %s: %s", ticker, exc)
        return None


def _load_cache() -> pd.DataFrame:
    with resources.files("portfolio_optimizer.resources").joinpath("prices_cache.csv").open("r") as f:
        df = pd.read_csv(f, parse_dates=["date"], index_col="date")
    return df


def load_prices(
    tickers: list[str],
    start: str | None = None,
    end: str | None = None,
    use_cache_only: bool = False,
) -> tuple[pd.DataFrame, bool]:
    """Return (wide DataFrame of adjusted close prices, used_live_data flag).

    Attempts a live stooq fetch for every requested ticker first. If any
    ticker fails to fetch live, the entire load falls back to the bundled
    cache so that the resulting panel is always aligned and gap-free rather
    than a patchwork of live and cached series with different vintages.
    """
    cache = _load_cache()
    missing = [t for t in tickers if t not in cache.columns]
    if missing:
        raise ValueError(f"tickers not available in bundled cache: {missing}")

    if not use_cache_only:
        live_series = {t: _fetch_one_from_stooq(t) for t in tickers}
        if all(s is not None for s in live_series.values()):
            df = pd.concat(live_series.values(), axis=1).sort_index().dropna()
            if start:
                df = df.loc[df.index >= pd.Timestamp(start)]
            if end:
                df = df.loc[df.index <= pd.Timestamp(end)]
            if len(df) > 250:
                return df[tickers], True
        logger.warning("falling back to bundled cached price data (data/prices_cache.csv)")

    df = cache[tickers].copy()
    if start:
        df = df.loc[df.index >= pd.Timestamp(start)]
    if end:
        df = df.loc[df.index <= pd.Timestamp(end)]
    return df, False


def cache_path() -> Path:
    return Path(str(resources.files("portfolio_optimizer.resources").joinpath("prices_cache.csv")))
