"""Default asset universe: ticker -> sector map and stooq symbol map.

The universe spans equities across nine GICS-like buckets plus a bond ETF
and a gold ETF, so sector-cap constraints and diversification metrics are
meaningful. SPY is carried alongside the optimizable universe purely as a
buy-and-hold benchmark; it is excluded from the optimizers by default
because it is a near-linear combination of large-cap equities and would
make the covariance matrix of an "everything" universe ill-conditioned.
"""

from __future__ import annotations

DEFAULT_SECTOR_MAP: dict[str, str] = {
    "AAPL": "Technology",
    "GOOG": "Technology",
    "META": "Communication Services",
    "T": "Communication Services",
    "JPM": "Financials",
    "MA": "Financials",
    "PFE": "Healthcare",
    "WMT": "Consumer Staples",
    "SBUX": "Consumer Discretionary",
    "GE": "Industrials",
    "XOM": "Energy",
    "TLT": "Fixed Income",
    "GLD": "Commodities",
}

BENCHMARK_TICKER = "SPY"

# Stooq uses lower-cased "<ticker>.us" symbols for US-listed names.
STOOQ_SYMBOLS: dict[str, str] = {
    t: f"{t.lower()}.us" for t in list(DEFAULT_SECTOR_MAP) + [BENCHMARK_TICKER]
}

# Approximate 2024 market capitalizations in USD billions, used only as a
# relative-size proxy to build Black-Litterman's equilibrium market-weight
# vector. These are rough public-knowledge figures, not fetched data, and
# the BL prior is not sensitive to small errors in relative sizing.
APPROX_MARKET_CAP_BN: dict[str, float] = {
    "AAPL": 3400.0,
    "GOOG": 2100.0,
    "META": 1500.0,
    "T": 150.0,
    "JPM": 600.0,
    "MA": 450.0,
    "PFE": 150.0,
    "WMT": 600.0,
    "SBUX": 100.0,
    "GE": 180.0,
    "XOM": 500.0,
    "TLT": 50.0,
    "GLD": 70.0,
}


def sectors_for(tickers: list[str]) -> dict[str, str]:
    return {t: DEFAULT_SECTOR_MAP.get(t, "Other") for t in tickers}


def market_weights_for(tickers: list[str]) -> dict[str, float]:
    caps = {t: APPROX_MARKET_CAP_BN.get(t, 1.0) for t in tickers}
    total = sum(caps.values())
    return {t: c / total for t, c in caps.items()}
