# Portfolio Intelligence Platform

Institutional-grade investment dashboard with live P&L, risk scoring, and Monte Carlo simulation.

**Stack:** React 19 · tRPC 11 · Express 4 · TypeScript · Tailwind CSS 3

## Features
- Live portfolio P&L with mock market prices
- Asset allocation & sector charts
- Monte Carlo simulation (GBM + Cholesky + VaR/CVaR)
- Research assistant for scenario and portfolio-impact analysis
- Risk scoring with concentration warnings
- Market intelligence across 5 asset classes
- Watchlists, CSV export, search, filter, sort

## Quick Start

```bash
cd server && npm install && npm run dev   # Backend :3001
cd client && npm install && npm run dev   # Frontend :5173
```

Open `http://localhost:5173`.

## Project Structure

```
client/   React + Vite + Tailwind frontend
server/   Express + tRPC API, in-memory data store
```

## Testing

```bash
cd server && npx tsc --noEmit   # typecheck the API
cd client && npx tsc --noEmit   # typecheck the frontend
```
