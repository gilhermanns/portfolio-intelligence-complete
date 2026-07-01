import { trpc } from "@/lib/trpc";
export function MarketTicker() {
  const marketQuery = trpc.market.getMarketOverview.useQuery({refetchInterval:60_000} as any);
  const indices = marketQuery.data?.indices ?? [];
  if (indices.length === 0) return null;
  const items = [...indices, ...indices];
  return (
    <div className="h-8 border-b border-border bg-card/80 overflow-hidden flex items-center">
      <div className="flex gap-8 whitespace-nowrap" style={{animation:"ticker 30s linear infinite"}}>
        {items.map((idx, i) => (
          <span key={i} className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">{idx.name}</span>
           <span className="text-foreground font-medium">{idx.value.toLocaleString("en-US",{maximumFractionDigits:2})}</span>
            <span className={idx.changePct >= 0 ? "text-green-400" : "text-red-400"}>{idx.changePct >= 0 ? "▲" : "▼"} {Math.abs(idx.changePct).toFixed(2)}%</span>
          </span>
        ))}
      </div>
    </div>
  );
}
