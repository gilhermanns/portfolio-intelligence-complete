import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { Activity, RefreshCw } from "lucide-react";
 
const SCENARIOS = ["Fed raises rates by 100bps","Equity market correction of 20%","Dollar strengthens 10% against major currencies","Oil spikes to $150/barrel","China growth slowdown"];
 
export default function PortfolioAnalysis() {
  const [scenario, setScenario] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const { toast } = useToast();
  const holdingsQuery = trpc.market.getPortfolioWithPnL.useQuery({ portfolioId: 1 });
  const holdings = (holdingsQuery.data ?? []).map((h) => ({ ticker: h.ticker, quantity: h.quantity, purchasePrice: h.purchasePrice, sector: h.sector, assetClass: h.assetClass }));
 
  const mutation = trpc.research.analyzePortfolioImpact.useMutation({
    onSuccess: (data) => { setResult(data.analysis); toast({ type: "success", title: "Analysis complete" }); },
    onError: (e) => toast({ type: "error", title: "Error", description: e.message }),
  });
 
  function handleAnalyze() { if (!scenario.trim() || !holdings.length) return; mutation.mutate({ holdings, scenario }); }
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">Impact Analysis</h1><p className="text-muted-foreground mt-1">Model how macro scenarios affect your portfolio</p></div>
      <Card>
        <CardContent className="pt-6 space-y-4">
          <Input placeholder="Describe a scenario…" value={scenario} onChange={(e) => setScenario(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleAnalyze()} />
          <div className="flex flex-wrap gap-2">{SCENARIOS.map((s) => <button key={s} onClick={() => setScenario(s)} className="text-xs px-3 py-1.5 rounded-full bg-muted text-muted-foreground hover:text-foreground transition-colors">{s}</button>)}</div>
          <Button onClick={handleAnalyze} disabled={mutation.isPending || !scenario.trim() || !holdings.length}>
            {mutation.isPending ? <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Analysing…</> : <><Activity className="h-4 w-4 mr-2" />Analyse Impact</>}
          </Button>
        </CardContent>
      </Card>
      {result && (
        <Card><CardHeader><CardTitle>Scenario Analysis</CardTitle></CardHeader>
        <CardContent><div className="prose-dark" dangerouslySetInnerHTML={{ __html: result.replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>").replace(/\n/g,"<br/>") }} /></CardContent></Card>
      )}
    </div>
  );
}
