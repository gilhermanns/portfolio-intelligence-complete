import { createTRPCReact } from "@trpc/react-query";
import { httpBatchLink } from "@trpc/client";
import type { AppRouter } from "../../../server/routers";
 
export const trpc = createTRPCReact<AppRouter>();
 
export function createTRPCClient() {
  return trpc.createClient({
    links: [httpBatchLink({ url: "/api/trpc", headers: () => ({ "x-user-id": "1" }) })],
  });
}
