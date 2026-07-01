import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DonutChart } from "@/components/charts/DonutChart";
import { HBarChart } from "@/components/charts/BarChart";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Activity, Globe } from "lucide-react";
 
const SECTOR_COLORS: Record<string,string> = { Technology:"#3b82f6", Financials:"#8b5cf6", Healthcare:"#10b981", "Fixed Income":"#f59e0b", Commodities:"#ef4444", Energy:"#f97316", Other:"#6b7280" };
const AC_COLORS: Record<string,string> = { equity:"#3b82f6", bond:"#10b981", commodity:"#f59e0b", crypto:"#8b5cf6", fx:"#ef4444", other:"#6b7280" };
 
function fmt(v: number) { return v >= 1_000_000 ? `$${(v/1_000_000).toFixed(2)}M` : v >= 1_000 ? `$${(v/1_000).toFixed(1)}K` : `$${v.toFixed(2)}`; }
 
export default function Dashboard() {
  const pnlQuery = trpc.market.getPortfolioWithPnL.useQuery({ portfolioId: 1 }, { refetchInterval: 30_000 });
  const marketQuery = trpc.market.getMarketOverview.useQuery();
  const intelQuery = trpc.market.getLatestIntelligence.useQuery();
  const holdings = pnlQuery.data ?? [];
  const market = marketQuery.data;
 
  const totalValue = holdings.reduce((s, h) => s + h.currentValue, 0);
  const totalPnl = holdings.reduce((s, h) => s + h.pnl, 0);
  const totalCost = holdings.reduce((s, h) => s + h.costBasis, 0);
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0;
  const dayChange = holdings.reduce((s, h) => s + h.dayChange * h.quantity, 0);
 
  const sectorMap: Record<string, number> = {};
  const acMap: Record<string, number> = {};
  for (const h of holdings) {
    sectorMap[h.sector] = (sectorMap[h.sector] ?? 0) + h.currentValue;
    acMap[h.assetClass] = (acMap[h.assetClass] ?? 0) + h.currentValue;
  }
  const sectorData = Object.entries(sectorMap).map(([label, value]) => ({ label, value, color: SECTOR_COLORS[label] ?? "#6b7280" }));
  const acData = Object.entries(acMap).map(([label, value]) => ({ label, value, color: AC_COLORS[label] ?? "#6b7280" }));
 
  if (pnlQuery.isLoading) return <div className="space-y-6"><div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-28" />)}</div></div>;
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">Dashboard</h1><p className="text-muted-foreground mt-1">Core Growth Portfolio — live overview</p></div>
 
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Portfolio Value", value: fmt(totalValue), sub: `${holdings.length} positions`, icon: Activity, color: "text-foreground" },
          { label: "Total P&L", value: fmt(Math.abs(totalPnl)), sub: `${totalPnlPct >= 0 ? "+" : ""}${totalPnlPct.toFixed(2)}%`, icon: totalPnl >= 0 ? TrendingUp : TrendingDown, color: totalPnl >= 0 ? "text-green-400" : "text-red-400" },
          { label: "Day Change", value: fmt(Math.abs(dayChange)), sub: dayChange >= 0 ? "Up today" : "Down today", icon: dayChange >= 0 ? TrendingUp : TrendingDown, color: dayChange >= 0 ? "text-green-400" : "text-red-400" },
          { label: "Market Sentiment", value: market?.sentiment ?? "—", sub: `Fear & Greed: ${market?.fearGreedIndex ?? "—"}`, icon: Globe, color: "text-accent" },
        ].map(({ label, value, sub, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div><p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{label}</p><p className={`text-2xl font-bold ${color}`}>{value}</p><p className="text-xs text-muted-foreground mt-1">{sub}</p></div>
                <Icon className={`h-5 w-5 ${color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
 
      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle>Asset Allocation</CardTitle></CardHeader><CardContent><DonutChart data={acData} size={180} thickness={32} centerLabel={fmt(totalValue)} centerSubLabel="Total" /></CardContent></Card>
        <Card><CardHeader><CardTitle>Sector Breakdown</CardTitle></CardHeader><CardContent><HBarChart data={sectorData.sort((a,b)=>b.value-a.value)} formatValue={(v)=>fmt(v)} maxValue={totalValue} /></CardContent></Card>
      </div>
 
      {/* Top holdings */}
      <Card>
        <CardHeader><CardTitle>Top Holdings</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...holdings].sort((a,b)=>b.currentValue-a.currentValue).slice(0,5).map((h) => (
              <div key={h.ticker} className="flex items-center justify-between py-2 border-b border-border/40 last:border-0">
                <div><p className="text-sm font-medium text-foreground">{h.ticker}</p><p className="text-xs text-muted-foreground">{h.sector}</p></div>
                <div className="text-right"><p className="text-sm font-medium text-foreground">{fmt(h.currentValue)}</p><p className={`text-xs ${h.pnlPct >= 0 ? "text-green-400" : "text-red-400"}`}>{h.pnlPct >= 0 ? "+" : ""}{h.pnlPct.toFixed(2)}%</p></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
 
      {/* Market indices + Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Market Indices</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {market?.indices.map((idx) => (
              <div key={idx.name} className="flex justify-between items-center py-1 border-b border-border/40 last:border-0">
                <span className="text-sm text-muted-foreground">{idx.name}</span>
                <div className="text-right"><span className="text-sm font-medium text-foreground">{idx.value.toLocaleString("en-US",{maximumFractionDigits:2})}</span><span className={`text-xs ml-2 ${idx.changePct >= 0 ? "text-green-400" : "text-red-400"}`}>{idx.changePct >= 0 ? "+" : ""}{idx.changePct.toFixed(2)}%</span></div>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Market Intelligence</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(intelQuery.data ?? []).slice(0,3).map((item) => (
              <div key={item.id} className="p-3 rounded-lg bg-muted/40 space-y-1">
                <div className="flex items-center justify-between"><span className="text-xs font-medium text-foreground">{item.assetClass}</span><span className={`text-xs px-2 py-0.5 rounded-full ${item.sentiment === "bullish" ? "bg-green-500/20 text-green-400" : item.sentiment === "bearish" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"}`}>{item.sentiment}</span></div>
                <p className="text-xs text-muted-foreground line-clamp-2">{item.summary}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
