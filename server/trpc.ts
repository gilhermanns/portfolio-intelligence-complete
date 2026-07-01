import { initTRPC, TRPCError } from "@trpc/server";
import type { Request, Response } from "express";
import { db, type User } from "./db";
 
export interface Context {
  user: User | null;
  req: Request;
  res: Response;
}
 
export function createContext({ req, res }: { req: Request; res: Response }): Context {
  const userId = req.headers["x-user-id"];
  const user = userId ? db.getUserById(Number(userId)) : db.getUserById(1);
  return { user, req, res };
}
 
const t = initTRPC.context<Context>().create();
export const router = t.router;
export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.user) throw new TRPCError({ code: "UNAUTHORIZED" });
  return next({ ctx: { ...ctx, user: ctx.user } });
});
