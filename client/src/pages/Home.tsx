import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { BarChart3, TrendingUp, ShieldAlert, Sigma } from "lucide-react";
 
export default function Home() {
  const [, nav] = useLocation();
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center">
            <BarChart3 className="h-6 w-6 text-accent-foreground" />
          </div>
          <div className="text-left">
            <h1 className="text-2xl font-bold text-foreground">Portfolio Intelligence</h1>
            <p className="text-sm text-muted-foreground">Institutional-grade investment dashboard</p>
          </div>
        </div>
        <p className="text-muted-foreground leading-relaxed">
          AI-powered portfolio management with real-time P&L tracking, Monte Carlo simulation, risk analysis, and market intelligence across all asset classes.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-left">
          {[
            { icon: TrendingUp,  label: "Live P&L",    desc: "Real-time portfolio tracking" },
            { icon: Sigma,       label: "Monte Carlo",  desc: "GBM + Cholesky simulation" },
            { icon: ShieldAlert, label: "Risk Analysis",desc: "VaR, CVaR, concentration" },
            { icon: BarChart3,   label: "AI Research",  desc: "Market intelligence & memos" },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="p-4 rounded-lg border border-border bg-card space-y-2">
              <Icon className="h-5 w-5 text-accent" />
              <p className="text-sm font-medium text-foreground">{label}</p>
              <p className="text-xs text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
        <Button size="lg" onClick={() => nav("/dashboard")}>
          Open Dashboard →
        </Button>
      </div>
    </div>
  );
}
