export interface User { id: number; email: string; name: string; role: string; createdAt: Date; }
export interface Portfolio { id: number; userId: number; name: string; description: string; createdAt: Date; }
export interface Holding { id: number; portfolioId: number; ticker: string; quantity: number; purchasePrice: number; sector: string; assetClass: string; addedAt: Date; }
export interface Watchlist { id: number; userId: number; name: string; createdAt: Date; }
export interface WatchlistItem { id: number; watchlistId: number; ticker: string; assetClass: string; addedAt: Date; }
export interface ResearchReport { id: number; userId: number; type: string; title: string; content: string; generatedAt: Date; }
export interface MarketIntelligence { id: number; assetClass: string; weekOf: string; summary: string; keyDrivers: string[]; sentiment: "bullish" | "bearish" | "neutral"; generatedAt: Date; }
 
let portfolioIdCounter = 2, holdingIdCounter = 8, watchlistIdCounter = 2;
let watchlistItemIdCounter = 6, reportIdCounter = 1;
 
const users: User[] = [{ id: 1, email: "demo@portfoliointelligence.com", name: "Demo User", role: "user", createdAt: new Date() }];
const portfolios: Portfolio[] = [{ id: 1, userId: 1, name: "Core Growth Portfolio", description: "Long-term equity growth holdings", createdAt: new Date() }];
const holdings: Holding[] = [
  { id: 1, portfolioId: 1, ticker: "AAPL", quantity: 150, purchasePrice: 178.5,  sector: "Technology",   assetClass: "equity",    addedAt: new Date() },
  { id: 2, portfolioId: 1, ticker: "MSFT", quantity: 80,  purchasePrice: 415.2,  sector: "Technology",   assetClass: "equity",    addedAt: new Date() },
  { id: 3, portfolioId: 1, ticker: "NVDA", quantity: 60,  purchasePrice: 87.5,   sector: "Technology",   assetClass: "equity",    addedAt: new Date() },
  { id: 4, portfolioId: 1, ticker: "JPM",  quantity: 100, purchasePrice: 198.3,  sector: "Financials",   assetClass: "equity",    addedAt: new Date() },
  { id: 5, portfolioId: 1, ticker: "JNJ",  quantity: 120, purchasePrice: 152.7,  sector: "Healthcare",   assetClass: "equity",    addedAt: new Date() },
  { id: 6, portfolioId: 1, ticker: "TLT",  quantity: 200, purchasePrice: 94.5,   sector: "Fixed Income", assetClass: "bond",      addedAt: new Date() },
  { id: 7, portfolioId: 1, ticker: "GLD",  quantity: 50,  purchasePrice: 215.0,  sector: "Commodities",  assetClass: "commodity", addedAt: new Date() },
];
const watchlists: Watchlist[] = [{ id: 1, userId: 1, name: "AI & Semiconductors", createdAt: new Date() }];
const watchlistItems: WatchlistItem[] = [
  { id: 1, watchlistId: 1, ticker: "NVDA", assetClass: "equity", addedAt: new Date() },
  { id: 2, watchlistId: 1, ticker: "AMD",  assetClass: "equity", addedAt: new Date() },
  { id: 3, watchlistId: 1, ticker: "INTC", assetClass: "equity", addedAt: new Date() },
  { id: 4, watchlistId: 1, ticker: "QCOM", assetClass: "equity", addedAt: new Date() },
  { id: 5, watchlistId: 1, ticker: "AVGO", assetClass: "equity", addedAt: new Date() },
];
const researchReports: ResearchReport[] = [];
const marketIntelligence: MarketIntelligence[] = [
  { id: 1, assetClass: "Equities", weekOf: "2026-06-09", summary: "US equities remained resilient despite mixed economic signals. The S&P 500 gained 1.2% driven by tech sector outperformance.", keyDrivers: ["Strong earnings revisions in semiconductors","Cooling inflation expectations","Fed pause on rate hikes","AI capex cycle sustaining momentum"], sentiment: "bullish", generatedAt: new Date() },
  { id: 2, assetClass: "Fixed Income", weekOf: "2026-06-09", summary: "Treasury yields dipped modestly as softer-than-expected jobs data renewed rate cut expectations. The 10Y/2Y curve steepened slightly.", keyDrivers: ["Weaker-than-expected NFP print","Fed rhetoric staying data-dependent","Strong demand at Treasury auctions","Tight credit spreads supporting carry"], sentiment: "neutral", generatedAt: new Date() },
  { id: 3, assetClass: "FX", weekOf: "2026-06-09", summary: "The USD weakened broadly as risk appetite improved. EUR/USD pushed above 1.10. EM currencies outperformed.", keyDrivers: ["Dollar index under pressure","Eurozone inflation stabilizing","EM risk-on sentiment","JPY intervention risk fading"], sentiment: "bearish", generatedAt: new Date() },
  { id: 4, assetClass: "Commodities", weekOf: "2026-06-09", summary: "Oil prices declined on demand concerns from China, while gold held near all-time highs.", keyDrivers: ["China demand uncertainty","Gold benefiting from de-dollarization","Copper demand from EV buildout","OPEC+ supply discipline"], sentiment: "neutral", generatedAt: new Date() },
  { id: 5, assetClass: "Crypto", weekOf: "2026-06-09", summary: "Bitcoin consolidated above $95,000 with institutional ETF inflows remaining strong.", keyDrivers: ["Spot Bitcoin ETF inflows","Regulatory clarity improving","Ethereum upgrade delays","DeFi TVL recovering"], sentiment: "bullish", generatedAt: new Date() },
];
 
export const db = {
  getUserById: (id: number) => users.find((u) => u.id === id) ?? null,
  getAllUsers: () => [...users],
  createPortfolio: (data: Omit<Portfolio, "id"|"createdAt">) => { const p: Portfolio = { id: portfolioIdCounter++, createdAt: new Date(), ...data }; portfolios.push(p); return p; },
  getPortfoliosByUserId: (userId: number) => portfolios.filter((p) => p.userId === userId),
  getPortfolioById: (id: number) => portfolios.find((p) => p.id === id) ?? null,
  deletePortfolio: (id: number) => { const i = portfolios.findIndex((p) => p.id === id); if (i !== -1) portfolios.splice(i, 1); },
  addHolding: (data: Omit<Holding, "id"|"addedAt">) => { const h: Holding = { id: holdingIdCounter++, addedAt: new Date(), ...data }; holdings.push(h); return h; },
  getHoldingsByPortfolioId: (portfolioId: number) => holdings.filter((h) => h.portfolioId === portfolioId),
  deleteHolding: (id: number) => { const i = holdings.findIndex((h) => h.id === id); if (i !== -1) holdings.splice(i, 1); },
  createWatchlist: (data: Omit<Watchlist, "id"|"createdAt">) => { const w: Watchlist = { id: watchlistIdCounter++, createdAt: new Date(), ...data }; watchlists.push(w); return w; },
  getWatchlistsByUserId: (userId: number) => watchlists.filter((w) => w.userId === userId),
  deleteWatchlist: (id: number) => { const i = watchlists.findIndex((w) => w.id === id); if (i !== -1) watchlists.splice(i, 1); },
  addWatchlistItem: (data: Omit<WatchlistItem, "id"|"addedAt">) => { const item: WatchlistItem = { id: watchlistItemIdCounter++, addedAt: new Date(), ...data }; watchlistItems.push(item); return item; },
  getWatchlistItems: (watchlistId: number) => watchlistItems.filter((i) => i.watchlistId === watchlistId),
  removeWatchlistItem: (id: number) => { const i = watchlistItems.findIndex((x) => x.id === id); if (i !== -1) watchlistItems.splice(i, 1); },
  createResearchReport: (data: Omit<ResearchReport, "id">) => { const r: ResearchReport = { id: reportIdCounter++, ...data }; researchReports.push(r); return r; },
  getReportsByUserId: (userId: number) => researchReports.filter((r) => r.userId === userId).sort((a, b) => b.generatedAt.getTime() - a.generatedAt.getTime()),
  getLatestIntelligence: () => marketIntelligence,
  getIntelligenceByAssetClass: (assetClass: string) => marketIntelligence.find((m) => m.assetClass.toLowerCase() === assetClass.toLowerCase()) ?? null,
};
