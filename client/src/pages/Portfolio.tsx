import { useState, useMemo } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import { Download, Search, ChevronUp, ChevronDown } from "lucide-react";
 
type SortKey = "ticker"|"currentValue"|"pnl"|"pnlPct"|"weight";
type SortDir = "asc"|"desc";
 
function fmt(v: number, d=2) { return `$${Math.abs(v).toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d})}`; }
 
export default function Portfolio() {
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [acFilter, setAcFilter] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("currentValue");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
 
  const pnlQuery = trpc.market.getPortfolioWithPnL.useQuery({ portfolioId: 1 }, { refetchInterval: 30_000 });
  const holdings = pnlQuery.data ?? [];
  const totalValue = holdings.reduce((s, h) => s + h.currentValue, 0);
 
  const rows = useMemo(() => {
    let filtered = holdings.filter((h) => {
      const matchSearch = h.ticker.toLowerCase().includes(search.toLowerCase()) || h.sector.toLowerCase().includes(search.toLowerCase());
      const matchAc = acFilter === "all" || h.assetClass === acFilter;
      return matchSearch && matchAc;
    });
    filtered = [...filtered].sort((a, b) => {
      const aVal = sortKey === "weight" ? a.currentValue/totalValue : (a as any)[sortKey];
      const bVal = sortKey === "weight" ? b.currentValue/totalValue : (b as any)[sortKey];
      return sortDir === "asc" ? aVal - bVal : bVal - aVal;
    });
    return filtered.map((h) => ({ ...h, weight: parseFloat(((h.currentValue/totalValue)*100).toFixed(2)) }));
  }, [holdings, search, acFilter, sortKey, sortDir, totalValue]);
 
  function toggleSort(key: SortKey) { if (sortKey === key) setSortDir((d) => d === "asc" ? "desc" : "asc"); else { setSortKey(key); setSortDir("desc"); } }
  function SortBtn({ k, label }: { k: SortKey; label: string }) {
    const active = sortKey === k;
    return <button onClick={() => toggleSort(k)} className={`flex items-center gap-1 text-xs font-medium ${active ? "text-accent" : "text-muted-foreground hover:text-foreground"}`}>{label}{active ? (sortDir === "desc" ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />) : null}</button>;
  }
 
  function exportCSV() {
    const header = "Ticker,Sector,AssetClass,Qty,AvgCost,CurrentPrice,Value,PnL,PnL%,Weight%";
    const rows2 = rows.map((h) => `${h.ticker},${h.sector},${h.assetClass},${h.quantity},${h.purchasePrice},${h.currentPrice},${h.currentValue},${h.pnl},${h.pnlPct},${h.weight}`).join("\n");
    const blob = new Blob([header+"\n"+rows2], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "portfolio.csv"; a.click();
    URL.revokeObjectURL(url);
    toast({ type: "success", title: "CSV exported" });
  }
 
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div><h1 className="text-3xl font-bold text-foreground">Holdings</h1><p className="text-muted-foreground mt-1">{holdings.length} positions · ${totalValue.toLocaleString("en-US",{maximumFractionDigits:0})} total</p></div>
        <Button variant="outline" size="sm" onClick={exportCSV}><Download className="h-4 w-4 mr-2" />Export CSV</Button>
      </div>
      <Card>
        <CardContent className="pt-4 space-y-3">
          <div className="flex gap-3 flex-wrap">
            <div className="relative flex-1 min-w-48"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" /><Input placeholder="Search ticker or sector…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" /></div>
            <Select value={acFilter} onChange={(e) => setAcFilter(e.target.value)} className="w-44">
              <option value="all">All asset classes</option>
              {["equity","bond","commodity","crypto","fx","other"].map((ac) => <option key={ac} value={ac}>{ac}</option>)}
            </Select>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-border">
                <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground">Ticker</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground">Sector</th>
                <th className="py-2 px-3 text-right"><SortBtn k="currentValue" label="Value" /></th>
                <th className="py-2 px-3 text-right"><SortBtn k="pnl" label="P&L $" /></th>
                <th className="py-2 px-3 text-right"><SortBtn k="pnlPct" label="P&L %" /></th>
                <th className="py-2 px-3 text-right"><SortBtn k="weight" label="Weight" /></th>
              </tr></thead>
              <tbody>
                {rows.map((h) => (
                  <tr key={h.id} className="border-b border-border/40 hover:bg-muted/20 transition-colors">
                    <td className="py-2.5 px-3"><span className="font-medium text-foreground">{h.ticker}</span><span className="text-xs text-muted-foreground ml-2">{h.quantity} sh.</span></td>
                    <td className="py-2.5 px-3 text-muted-foreground text-xs">{h.sector}</td>
                    <td className="py-2.5 px-3 text-right font-medium text-foreground">{fmt(h.currentValue)}</td>
                    <td className={`py-2.5 px-3 text-right font-medium ${h.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>{h.pnl >= 0 ? "+" : "-"}{fmt(h.pnl)}</td>
                    <td className={`py-2.5 px-3 text-right ${h.pnlPct >= 0 ? "text-green-400" : "text-red-400"}`}>{h.pnlPct >= 0 ? "+" : ""}{h.pnlPct.toFixed(2)}%</td>
                    <td className="py-2.5 px-3 text-right text-muted-foreground">{h.weight}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
