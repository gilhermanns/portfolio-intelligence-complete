import { router } from "../trpc";
import { portfolioRouter } from "./portfolio";
import { holdingsRouter } from "./holdings";
import { watchlistRouter } from "./watchlist";
import { marketRouter } from "./market";
import { researchRouter } from "./research";
import { montecarloRouter } from "./montecarlo";
 
export const appRouter = router({
  portfolio: portfolioRouter,
  holdings: holdingsRouter,
  watchlist: watchlistRouter,
  market: marketRouter,
  research: researchRouter,
  montecarlo: montecarloRouter,
});
 
export type AppRouter = typeof appRouter;
