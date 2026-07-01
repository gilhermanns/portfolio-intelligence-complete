import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SimulationChart } from "@/components/charts/SimulationChart";
import { HistogramChart } from "@/components/charts/HistogramChart";
import { useToast } from "@/components/ui/toast";
import { TrendingDown, TrendingUp, AlertTriangle, BarChart3, RefreshCw, Play, Info } from "lucide-react";
 
const TIME_OPTIONS = [{ label:"1 Year",months:12},{label:"3 Years",months:36},{label:"5 Years",months:60},{label:"10 Years",months:120},{label:"20 Years",months:240}];
const SIM_OPTIONS = [500,1000,2000,5000,10000];
 
function fmt(v:number):string{return`$${Math.abs(v).toLocaleString("en-US",{maximumFractionDigits:0})}`;}
 
function StatCard({ label,value,sub,color="text-foreground",icon:Icon,tooltip }:{label:string;value:string;sub?:string;color?:string;icon?:any;tooltip?:string;}) {
  return (
    <div className="p-4 rounded-lg border border-border bg-card space-y-1">
      <div className="flex items-center gap-1.5">
        {Icon && <Icon className={`h-3.5 w-3.5 ${color}`} />}
        <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
        {tooltip && <span title={tooltip} className="cursor-help text-muted-foreground/50 hover:text-muted-foreground"><Info className="h-3 w-3" /></span>}
      </div>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}
 
type SimResult = NonNullable<ReturnType<typeof trpc.montecarlo.run.useMutation>["data"]>;
 
export default function MonteCarlo() {
  const [timeHorizonMonths, setTimeHorizonMonths] = useState(60);
  const [numSimulations, setNumSimulations] = useState(1000);
  const [result, setResult] = useState<SimResult | null>(null);
  const { toast } = useToast();
 
  const portfoliosQuery = trpc.portfolio.list.useQuery();
  const activePortfolio = (portfoliosQuery.data ?? [])[0];
 
  const runMutation = trpc.montecarlo.run.useMutation({
    onSuccess: (data) => { setResult(data); toast({ type:"success", title:"Simulation complete", description:`${numSimulations.toLocaleString()} paths × ${timeHorizonMonths/12}Y` }); },
    onError: (e) => toast({ type:"error", title:"Simulation failed", description:e.message }),
  });
 
  const stats = result?.statistics;
 
  return (
    <div className="space-y-8">
      <div><h1 className="text-3xl font-bold text-foreground">Monte Carlo Simulation</h1><p className="text-muted-foreground mt-1">Stochastic portfolio forecasting using GBM with Cholesky-correlated asset returns</p></div>
 
      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><BarChart3 className="h-4 w-4 text-accent" />Simulation Parameters</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Time Horizon</p>
            <div className="flex gap-2 flex-wrap">
              {TIME_OPTIONS.map((opt) => <button key={opt.months} onClick={() => setTimeHorizonMonths(opt.months)} className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${timeHorizonMonths===opt.months?"bg-accent text-accent-foreground":"bg-muted text-muted-foreground hover:text-foreground"}`}>{opt.label}</button>)}
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Number of Simulations</p>
            <div className="flex gap-2 flex-wrap">
              {SIM_OPTIONS.map((n) => <button key={n} onClick={() => setNumSimulations(n)} className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${numSimulations===n?"bg-accent text-accent-foreground":"bg-muted text-muted-foreground hover:text-foreground"}`}>{n.toLocaleString()}</button>)}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {["GBM with Itô correction","Box-Muller normal sampling","Cholesky-correlated asset classes","95% & 99% VaR + CVaR"].map((tag) => <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>)}
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={() => activePortfolio && runMutation.mutate({ portfolioId:activePortfolio.id, timeHorizonMonths, numSimulations })} disabled={!activePortfolio || runMutation.isPending}>
              {runMutation.isPending ? <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Running {numSimulations.toLocaleString()} paths…</> : <><Play className="h-4 w-4 mr-2" />Run Simulation</>}
            </Button>
            {!activePortfolio && <p className="text-sm text-yellow-400 flex items-center gap-1"><AlertTriangle className="h-4 w-4" /> Add a portfolio first</p>}
            {result && <p className="text-xs text-muted-foreground">Portfolio: {fmt(result.initialValue)} · {numSimulations.toLocaleString()} paths · {timeHorizonMonths/12}Y horizon</p>}
          </div>
        </CardContent>
      </Card>
 
      {result && stats && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <StatCard label="Initial Value" value={fmt(stats.initialValue)} icon={BarChart3} sub="Current portfolio" />
            <StatCard label="Median Outcome" value={fmt(stats.median)} sub={`${stats.annualizedReturn>=0?"+":""}${stats.annualizedReturn}% p.a.`} color={stats.median>=stats.initialValue?"text-green-400":"text-red-400"} icon={stats.median>=stats.initialValue?TrendingUp:TrendingDown} />
            <StatCard label="95% VaR (loss)" value={fmt(stats.lossAtVar95)} sub={`Floor: ${fmt(stats.var95)}`} color="text-red-400" icon={AlertTriangle} tooltip="Max loss at 95% confidence — only 5% of simulations end worse" />
            <StatCard label="95% CVaR (avg tail)" value={fmt(stats.lossAtCvar95)} sub={`Avg floor: ${fmt(stats.cvar95)}`} color="text-orange-400" icon={AlertTriangle} tooltip="Average loss in the worst 5% of scenarios" />
            <StatCard label="Prob. of Loss" value={`${stats.probLoss}%`} sub="Ending below start" color={stats.probLoss>30?"text-red-400":stats.probLoss>15?"text-yellow-400":"text-green-400"} />
            <StatCard label="+20% Probability" value={`${stats.probGain20}%`} sub="Ending 20%+ above start" color="text-green-400" />
            <StatCard label="Best Case" value={fmt(stats.bestCase)} sub="Highest simulated outcome" color="text-green-400" />
            <StatCard label="Worst Case" value={fmt(stats.worstCase)} sub="Lowest simulated outcome" color="text-red-400" />
          </div>
 
          <Card className="border-accent/20 bg-accent/5">
            <CardContent className="pt-4 pb-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div><p className="font-medium text-foreground mb-1">VaR 95%: <span className="text-red-400">{fmt(stats.lossAtVar95)} loss threshold</span></p><p className="text-muted-foreground text-xs">95% probability your portfolio will not lose more than <strong className="text-foreground">{fmt(stats.lossAtVar95)}</strong> over {timeHorizonMonths/12} years.</p></div>
                <div><p className="font-medium text-foreground mb-1">CVaR 95%: <span className="text-orange-400">{fmt(stats.lossAtCvar95)} avg tail loss</span></p><p className="text-muted-foreground text-xs">In the worst 5% of scenarios, average loss is <strong className="text-foreground">{fmt(stats.lossAtCvar95)}</strong>. CVaR captures severity of extreme losses, not just the threshold.</p></div>
              </div>
            </CardContent>
          </Card>
 
          <Card>
            <CardHeader><div className="flex items-center justify-between"><CardTitle>Simulated Portfolio Paths</CardTitle><div className="flex gap-2 text-xs text-muted-foreground"><span>{numSimulations.toLocaleString()} simulations</span><span>·</span><span>{timeHorizonMonths/12}Y horizon</span></div></div></CardHeader>
            <CardContent><SimulationChart samplePaths={result.samplePaths} percentilePaths={result.percentilePaths} initialValue={result.initialValue} timeHorizonMonths={timeHorizonMonths} /></CardContent>
          </Card>
 
          <Card>
            <CardHeader><CardTitle>Final Value Distribution</CardTitle><p className="text-sm text-muted-foreground">Distribution of {numSimulations.toLocaleString()} portfolio values at year {timeHorizonMonths/12}. Red = loss, Green = gain.</p></CardHeader>
            <CardContent><HistogramChart data={result.histogram} /></CardContent>
          </Card>
 
          <Card>
            <CardHeader><CardTitle>Full Risk Report</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-3">
                {[
                  ["Initial Portfolio Value", fmt(stats.initialValue)],["Median Final Value", fmt(stats.median)],["Mean Final Value", fmt(stats.mean)],
                  ["Annualised Return (median)", `${stats.annualizedReturn>=0?"+":""}${stats.annualizedReturn}%`],["─────────────",""],
                  ["VaR 95% (loss threshold)", fmt(stats.lossAtVar95)],["VaR 99% (loss threshold)", fmt(stats.initialValue-stats.var99)],
                  ["CVaR 95% (avg tail loss)", fmt(stats.lossAtCvar95)],["CVaR 99% (avg tail loss)", fmt(stats.initialValue-stats.cvar99)],["─────────────",""],
                  ["Probability of any loss", `${stats.probLoss}%`],["Probability of +20% gain", `${stats.probGain20}%`],
                  ["Probability of doubling", `${stats.probDouble}%`],["─────────────",""],
                  ["Best case scenario", fmt(stats.bestCase)],["Worst case scenario", fmt(stats.worstCase)],
                ].map(([label,value]) => label.startsWith("─") ? <div key={label} className="col-span-full border-t border-border my-1" /> : (
                  <div key={label} className="flex justify-between py-1 border-b border-border/40">
                    <span className="text-sm text-muted-foreground">{label}</span>
                    <span className="text-sm font-medium text-foreground">{value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
 
          <Card className="border-border/50">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground leading-relaxed"><strong className="text-foreground">Methodology:</strong> GBM with Itô correction <em>(μ − σ²/2)Δt</em> per monthly step. Cholesky decomposition of 6×6 asset-class correlation matrix. Box-Muller transform for standard normals. Parameters: Equity μ=9.8% σ=17%, Bond μ=3.5% σ=5.5%, Commodity μ=4.5% σ=18%, Crypto μ=35% σ=70%. <strong className="text-foreground">Not financial advice.</strong></p>
            </CardContent>
          </Card>
        </>
      )}
 
      {!result && !runMutation.isPending && (
        <Card><CardContent className="py-20 text-center space-y-4"><div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mx-auto"><BarChart3 className="h-8 w-8 text-accent" /></div><p className="text-lg font-medium text-foreground">Run your first simulation</p><p className="text-sm text-muted-foreground max-w-sm mx-auto">Configure the time horizon and number of paths above, then click "Run Simulation".</p></CardContent></Card>
      )}
    </div>
  );
}
Das war der letzte fehlende Teil. Das komplette Projekt ist jetzt vollständig im Chat — alle 35+ Dateien mit vollem Code, von Root-Config bis zur letzten Page.
