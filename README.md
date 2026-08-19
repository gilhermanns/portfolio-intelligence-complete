# Portfolio Intelligence Platform

[![Client and Server Build](https://github.com/gilhermanns/portfolio-intelligence-complete/actions/workflows/build.yml/badge.svg)](https://github.com/gilhermanns/portfolio-intelligence-complete/actions/workflows/build.yml)

A **portfolio-research dashboard prototype** that brings allocation, risk, scenario analysis, market intelligence and watchlists into one review workflow. It is designed to demonstrate application architecture and finance-oriented decision support — not to provide live investment advice or production portfolio valuation.

> **Data scope:** The current application uses mock prices and an in-memory data store. “P&L”, risk and scenario views are therefore reproducible product demonstrations, not live client reporting.

## What an analyst can review

| Workflow | Current capability | Review question |
|---|---|---|
| Portfolio overview | Allocation, sector breakdown and mock P&L views | Where are the largest exposures? |
| Risk analysis | Concentration warnings, risk scoring and Monte Carlo / VaR-CVaR calculations | Which assumptions and concentrations drive risk? |
| Market intelligence | Cross-asset market context and research-assistant prompts | What recent market information should frame the discussion? |
| Watchlists & exports | Watchlists, search, filters, sorting and CSV export | Can the analysis be reviewed and carried into another workflow? |

## Architecture

```text
React + Vite client
        │ typed tRPC calls
        ▼
Express + tRPC API
        │
        ├── portfolio, holdings and risk calculations
        ├── scenario / Monte Carlo analysis
        └── in-memory demonstration data
```

The separation between frontend, typed API and calculation modules keeps the project extensible while making the current prototype boundary explicit.

## Run locally

Install dependencies in each package, then start the API and client in separate terminals:

```bash
# Terminal 1
cd server
npm ci
npm run dev

# Terminal 2
cd client
npm ci
npm run dev
```

Open the Vite URL displayed in the second terminal. The API default is port `3001`; the Vite development server normally starts on port `5173`.

## Build and validation

The repository has a GitHub Actions workflow that performs the same production builds on pushes and pull requests. The client imports the API router type, so the server dependencies are installed before the client TypeScript build.

```bash
cd server && npm ci && npm run build
cd ../client && npm ci && npm run build
```

## Related quantitative projects

The `projects/` directory contains seven independent Python projects: portfolio optimization, walk-forward backtesting, order-book microstructure simulation, a risk dashboard, an options / volatility lab, sentiment research and a credit-risk model. Each project has its own README, tests and versioned results. See [`projects/README.md`](projects/README.md) for the index.

## Limitations

- Data is currently mock and in-memory; there is no persistence layer or live market-data integration.
- Risk and scenario outputs depend on model inputs and are for analytical discussion, not recommendations.
- A later production version would require authenticated users, persistent holdings, documented data licensing and independent controls around market-data quality.

---

*Entwickelt mit Unterstützung von Claude Code (Anthropic).*
*Research and educational prototype; not investment advice.*
