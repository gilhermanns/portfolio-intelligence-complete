import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { db } from "../db";
import { TRPCError } from "@trpc/server";
 
export const holdingsRouter = router({
  list: protectedProcedure
    .input(z.object({ portfolioId: z.number() }))
    .query(({ ctx, input }) => {
      const p = db.getPortfolioById(input.portfolioId);
      if (!p || p.userId !== ctx.user.id) throw new TRPCError({ code: "NOT_FOUND" });
      return db.getHoldingsByPortfolioId(input.portfolioId);
    }),
  add: protectedProcedure
    .input(z.object({
      portfolioId: z.number(),
      ticker: z.string().min(1).max(10).toUpperCase(),
      quantity: z.number().positive(),
      purchasePrice: z.number().positive(),
      sector: z.string().default("Unknown"),
      assetClass: z.enum(["equity","bond","commodity","crypto","fx","other"]),
    }))
    .mutation(({ ctx, input }) => {
      const p = db.getPortfolioById(input.portfolioId);
      if (!p || p.userId !== ctx.user.id) throw new TRPCError({ code: "NOT_FOUND" });
      return db.addHolding(input);
    }),
  delete: protectedProcedure
    .input(z.object({ holdingId: z.number() }))
    .mutation(({ input }) => { db.deleteHolding(input.holdingId); return { success: true }; }),
});
