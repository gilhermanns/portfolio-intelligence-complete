import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { db } from "../db";
 
export const watchlistRouter = router({
  list: protectedProcedure.query(({ ctx }) => db.getWatchlistsByUserId(ctx.user.id)),
  create: protectedProcedure
    .input(z.object({ name: z.string().min(1) }))
    .mutation(({ ctx, input }) => db.createWatchlist({ userId: ctx.user.id, name: input.name })),
  delete: protectedProcedure
    .input(z.object({ watchlistId: z.number() }))
    .mutation(({ input }) => { db.deleteWatchlist(input.watchlistId); return { success: true }; }),
  getItems: protectedProcedure
    .input(z.object({ watchlistId: z.number() }))
    .query(({ input }) => db.getWatchlistItems(input.watchlistId)),
  addItem: protectedProcedure
    .input(z.object({ watchlistId: z.number(), ticker: z.string().min(1).max(10).toUpperCase(), assetClass: z.string().default("equity") }))
    .mutation(({ input }) => db.addWatchlistItem(input)),
  removeItem: protectedProcedure
    .input(z.object({ watchlistItemId: z.number() }))
    .mutation(({ input }) => { db.removeWatchlistItem(input.watchlistItemId); return { success: true }; }),
});
