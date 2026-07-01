import express from "express";
import cors from "cors";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { appRouter } from "./routers";
import { createContext } from "./trpc";
 
const app = express();
const PORT = process.env.PORT || 3001;
 
app.use(cors({ origin: "http://localhost:5173", credentials: true }));
app.use(express.json());
app.use("/api/trpc", createExpressMiddleware({ router: appRouter, createContext }));
app.get("/health", (_, res) => res.json({ status: "ok", timestamp: new Date() }));
 
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
