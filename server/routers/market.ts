import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { db } from "../db";
 
const KNOWN_PRICES: Record<string, { price: number; changePct: number }> = {
  AAPL: { price: 213.49, changePct: 0.82 },  MSFT: { price: 447.22, changePct: 1.14 },
  NVDA: { price: 131.38, changePct: 2.67 },  GOOGL: { price: 178.02, changePct: -0.43 },
  AMZN: { price: 196.45, changePct: 0.61 },  META: { price: 549.10, changePct: 1.32 },
  TSLA: { price: 177.58, changePct: -1.85 }, JPM: { price: 233.41, changePct: 0.29 },
  JNJ:  { price: 148.73, changePct: -0.17 }, TLT: { price: 88.42,  changePct: 0.34 },
  GLD:  { price: 231.55, changePct: 0.51 },  AMD: { price: 164.23, changePct: 3.11 },
  INTC: { price: 22.87,  changePct: -1.24 }, QCOM: { price: 178.64, changePct: 1.05 },
  AVGO: { price: 241.15, changePct: 0.88 },  V:    { price: 289.45, changePct: 0.35 },
  GS:   { price: 544.32, changePct: 0.74 },  XOM:  { price: 118.76, changePct: -0.56 },
};
 
function getMockPrice(ticker: string) {
  const known = KNOWN_PRICES[ticker.toUpperCase()];
  if (known) {
    const change = parseFloat((known.price * known.changePct / 100).toFixed(2));
    return { price: known.price, change, changePct: known.changePct };
  }
  const seed = ticker.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const price = parseFloat((50 + (seed % 900) + (seed % 50) * 0.37).toFixed(2));
  const changePct = parseFloat((((seed % 20) - 10) * 0.3).toFixed(2));
  return { price, change: parseFloat((price * changePct / 100).toFixed(2)), changePct };
}
 
export const marketRouter = router({
  getLatestIntelligence: protectedProcedure.query(() => db.getLatestIntelligence()),
  getIntelligenceByAssetClass: protectedProcedure
    .input(z.object({ assetClass: z.string() }))
    .query(({ input }) => db.getIntelligenceByAssetClass(input.assetClass)),
  getQuote: protectedProcedure
    .input(z.object({ ticker: z.string() }))
    .query(({ input }) => getMockPrice(input.ticker)),
  getBatchQuotes: protectedProcedure
    .input(z.object({ tickers: z.array(z.string()) }))
    .query(({ input }) => input.tickers.map((ticker) => ({ ticker, ...getMockPrice(ticker) }))),
  getMarketOverview: protectedProcedure.query(() => ({
    indices: [
      { name: "S&P 500",      value: 5847.32,  change: 23.4,   changePct: 0.42 },
      { name: "NASDAQ",       value: 18923.11, change: 124.5,  changePct: 0.66 },
      { name: "DOW",          value: 42156.78, change: -45.2,  changePct: -0.11 },
      { name: "Russell 2000", value: 2187.44,  change: 8.7,    changePct: 0.4 },
      { name: "VIX",          value: 14.23,    change: -0.87,  changePct: -5.77 },
    ],
    sentiment: "Cautiously Bullish",
    fearGreedIndex: 62,
  })),
  getPortfolioWithPnL: protectedProcedure
    .input(z.object({ portfolioId: z.number() }))
    .query(({ input }) => {
      const holdings = db.getHoldingsByPortfolioId(input.portfolioId);
      return holdings.map((h) => {
        const quote = getMockPrice(h.ticker);
        const costBasis = h.quantity * h.purchasePrice;
        const currentValue = h.quantity * quote.price;
        const pnl = currentValue - costBasis;
        return {
          ...h,
          currentPrice: quote.price,
          dayChange: quote.change,
          dayChangePct: quote.changePct,
          currentValue: parseFloat(currentValue.toFixed(2)),
          costBasis: parseFloat(costBasis.toFixed(2)),
          pnl: parseFloat(pnl.toFixed(2)),
          pnlPct: parseFloat(((pnl / costBasis) * 100).toFixed(2)),
        };
      });
    }),
});
