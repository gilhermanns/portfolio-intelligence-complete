import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DonutChart } from "@/components/charts/DonutChart";
import { Skeleton } from "@/components/ui/skeleton";
import { ShieldAlert, AlertTriangle } from "lucide-react";
 
const AC_COLORS: Record<string,string> = { equity:"#3b82f6", bond:"#10b981", commodity:"#f59e0b", crypto:"#8b5cf6", fx:"#ef4444", other:"#6b7280" };
 
function RiskMeter({ score }: { score: number }) {
  const pct = score / 10;
  const color = pct > 0.7 ? "#ef4444" : pct > 0.4 ? "#f59e0b" : "#10b981";
  const r = 60, cx = 80, cy = 80;
  const startAngle = -Math.PI * 0.8, endAngle = Math.PI * 0.8;
  const arcLen = endAngle - startAngle;
  const bgEnd = endAngle, fillEnd = startAngle + arcLen * pct;
  const toXY = (a: number) => [cx + r * Math.cos(a), cy + r * Math.sin(a)] as [number, number];
  const arcPath = (s: number, e: number) => { const [sx,sy]=toXY(s); const [ex,ey]=toXY(e); const large=e-s>Math.PI?1:0; return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`; };
  return (
    <div className="flex flex-col items-center">
      <svg width={160} height={110}>
        <path d={arcPath(startAngle, bgEnd)} fill="none" stroke="hsl(var(--muted))" strokeWidth={14} strokeLinecap="round" />
        <path d={arcPath(startAngle, fillEnd)} fill="none" stroke={color} strokeWidth={14} strokeLinecap="round" />
        <text x={cx} y={cy+8} textAnchor="middle" style={{fontSize:24,fontWeight:700,fill:color}}>{score}</text>
        <text x={cx} y={cy+24} textAnchor="middle" style={{fontSize:11,fill:"hsl(var(--muted-foreground))"}}>/ 10</text>
      </svg>
      <p className="text-sm font-medium" style={{color}}>{score > 7 ? "High Risk" : score > 4 ? "Moderate Risk" : "Low Risk"}</p>
    </div>
  );
}
 
export default function RiskAnalysis() {
  const holdingsQuery = trpc.market.getPortfolioWithPnL.useQuery({ portfolioId: 1 });
  const holdings = (holdingsQuery.data ?? []).map((h) => ({ ticker: h.ticker, quantity: h.quantity, purchasePrice: h.purchasePrice, sector: h.sector, assetClass: h.assetClass }));
 
  const riskQuery = trpc.research.analyzeConcentrationRisks.useMutation();
  const risk = riskQuery.data;
 
  if (!risk && holdings.length > 0 && !riskQuery.isPending) { riskQuery.mutate({ holdings }); }
  if (holdingsQuery.isLoading) return <Skeleton className="h-96" />;
 
  const acData = (risk?.assetClassBreakdown ?? []).map((a) => ({ label: a.assetClass, value: a.percentage, color: AC_COLORS[a.assetClass] ?? "#6b7280" }));
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">Risk Analysis</h1><p className="text-muted-foreground mt-1">Portfolio concentration and risk scoring</p></div>
      {risk && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="flex flex-col items-center justify-center p-6"><CardTitle className="mb-4 flex items-center gap-2"><ShieldAlert className="h-4 w-4" />Risk Score</CardTitle><RiskMeter score={risk.riskScore} /></Card>
            <Card className="lg:col-span-2"><CardHeader><CardTitle>Asset Class Mix</CardTitle></CardHeader><CardContent><DonutChart data={acData} size={160} thickness={28} /></CardContent></Card>
          </div>
          {risk.warnings.length > 0 && (
            <div className="space-y-2">
              {risk.warnings.map((w) => <div key={w} className="flex items-start gap-3 p-4 rounded-lg border border-red-500/30 bg-red-500/5"><AlertTriangle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" /><p className="text-sm text-foreground">{w}</p></div>)}
            </div>
          )}
          <Card>
            <CardHeader><CardTitle>Sector Concentration</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {risk.sectorConcentration.map((s) => (
                <div key={s.sector}>
                  <div className="flex justify-between text-xs mb-1"><span className="text-muted-foreground">{s.sector}</span><span className={`font-medium ${s.risk === "High" ? "text-red-400" : s.risk === "Medium" ? "text-yellow-400" : "text-green-400"}`}>{s.percentage}% · {s.risk}</span></div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden"><div className="h-full rounded-full transition-all" style={{width:`${s.percentage}%`,background:s.risk==="High"?"#ef4444":s.risk==="Medium"?"#f59e0b":"#10b981"}} /></div>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {risk.recommendations.map((r) => <div key={r} className="flex items-start gap-2 text-sm text-muted-foreground"><span className="text-accent mt-0.5">→</span>{r}</div>)}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
