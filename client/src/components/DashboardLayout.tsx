import { ReactNode, useState } from "react";
import { Link, useLocation } from "wouter";
import { BarChart3, TrendingUp, Newspaper, MessageSquare, ShieldAlert, Eye, LogOut, ChevronLeft, ChevronRight, Activity, Sigma, FileText, Menu } from "lucide-react";
import { Button } from "./ui/button";
import { MarketTicker } from "./MarketTicker";
 
const navGroups = [
  { label: "Overview", items: [{ label: "Dashboard", href: "/dashboard", icon: BarChart3 }] },
  { label: "Portfolio", items: [
    { label: "Holdings", href: "/portfolio", icon: TrendingUp },
    { label: "Impact Analysis", href: "/portfolio-analysis", icon: Activity },
    { label: "Risk Analysis", href: "/risk-analysis", icon: ShieldAlert },
    { label: "Monte Carlo", href: "/monte-carlo", icon: Sigma },
    { label: "Watchlists", href: "/watchlists", icon: Eye },
  ]},
  { label: "Research", items: [
    { label: "Market Intelligence", href: "/market-intelligence", icon: Newspaper },
    { label: "AI Assistant", href: "/research-assistant", icon: MessageSquare },
    { label: "Reports", href: "/research", icon: FileText },
  ]},
];
 
function NavItem({ href, label, icon: Icon, isActive, collapsed }: { href: string; label: string; icon: any; isActive: boolean; collapsed: boolean }) {
  return (
    <Link href={href}>
      <a className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm font-medium group ${isActive ? "bg-accent/15 text-accent" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"} ${collapsed ? "justify-center" : ""}`} title={collapsed ? label : undefined}>
        <Icon className={`h-4 w-4 flex-shrink-0 ${isActive ? "text-accent" : "text-muted-foreground group-hover:text-foreground"}`} />
        {!collapsed && <span>{label}</span>}
        {isActive && !collapsed && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent" />}
      </a>
    </Link>
  );
}
 
export default function DashboardLayout({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
 
  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-4 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
          <BarChart3 className="h-4 w-4 text-accent-foreground" />
        </div>
        {!collapsed && <div><p className="text-sm font-bold text-foreground leading-tight">Portfolio</p><p className="text-xs text-muted-foreground leading-tight">Intelligence</p></div>}
      </div>
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {navGroups.map((group) => (
          <div key={group.label}>
            {!collapsed && <p className="px-3 mb-1 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{group.label}</p>}
            <div className="space-y-0.5">
              {group.items.map((item) => <NavItem key={item.href} href={item.href} label={item.label} icon={item.icon} isActive={location === item.href} collapsed={collapsed} />)}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t border-border p-3 space-y-2">
        {!collapsed && <div className="px-2 py-1.5 rounded-lg bg-muted/40"><p className="text-xs font-medium text-foreground">Demo User</p><p className="text-xs text-muted-foreground">demo@portfoliointelligence.com</p></div>}
        <Button variant="ghost" size="sm" className={`w-full text-muted-foreground hover:text-foreground ${collapsed ? "justify-center" : "justify-start gap-2"}`}>
          <LogOut className="h-4 w-4 flex-shrink-0" />
          {!collapsed && "Logout"}
        </Button>
      </div>
    </div>
  );
 
  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <aside className={`hidden md:flex flex-col relative border-r border-border bg-card transition-all duration-200 ${collapsed ? "w-16" : "w-60"}`}>
        {sidebarContent}
        <button onClick={() => setCollapsed(!collapsed)} className="absolute -right-3 top-[72px] z-10 bg-card border border-border rounded-full p-0.5 text-muted-foreground hover:text-foreground shadow-sm">
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-64 bg-card border-r border-border">{sidebarContent}</aside>
        </div>
      )}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-shrink-0">
          <MarketTicker />
          <div className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-border bg-card">
            <button onClick={() => setMobileOpen(true)} className="text-muted-foreground"><Menu className="h-5 w-5" /></button>
            <span className="font-semibold text-foreground text-sm">Portfolio Intelligence</span>
          </div>
        </div>
        <main className="flex-1 overflow-y-auto"><div className="p-6 md:p-8 max-w-7xl mx-auto">{children}</div></main>
      </div>
    </div>
  );
}
