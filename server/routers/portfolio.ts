import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { db } from "../db";
import { TRPCError } from "@trpc/server";
 
export const portfolioRouter = router({
  list: protectedProcedure.query(({ ctx }) => db.getPortfoliosByUserId(ctx.user.id)),
  create: protectedProcedure
    .input(z.object({ name: z.string().min(1), description: z.string().default("") }))
    .mutation(({ ctx, input }) => db.createPortfolio({ userId: ctx.user.id, ...input })),
  delete: protectedProcedure
    .input(z.object({ portfolioId: z.number() }))
    .mutation(({ ctx, input }) => {
      const p = db.getPortfolioById(input.portfolioId);
      if (!p || p.userId !== ctx.user.id) throw new TRPCError({ code: "NOT_FOUND" });
      db.deletePortfolio(input.portfolioId);
      return { success: true };
    }),
  getById: protectedProcedure
    .input(z.object({ portfolioId: z.number() }))
    .query(({ ctx, input }) => {
      const p = db.getPortfolioById(input.portfolioId);
      if (!p || p.userId !== ctx.user.id) throw new TRPCError({ code: "NOT_FOUND" });
      return p;
    }),
});
