import { Switch, Route, Redirect } from "wouter";
import DashboardLayout from "./components/DashboardLayout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import MarketIntelligence from "./pages/MarketIntelligence";
import ResearchAssistant from "./pages/ResearchAssistant";
import PortfolioAnalysis from "./pages/PortfolioAnalysis";
import RiskAnalysis from "./pages/RiskAnalysis";
import Research from "./pages/Research";
import Watchlists from "./pages/Watchlists";
import MonteCarlo from "./pages/MonteCarlo";
 
function DashboardPage({ children }: { children: React.ReactNode }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
 
export default function App() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/dashboard"><DashboardPage><Dashboard /></DashboardPage></Route>
      <Route path="/portfolio"><DashboardPage><Portfolio /></DashboardPage></Route>
      <Route path="/market-intelligence"><DashboardPage><MarketIntelligence /></DashboardPage></Route>
      <Route path="/research-assistant"><DashboardPage><ResearchAssistant /></DashboardPage></Route>
      <Route path="/portfolio-analysis"><DashboardPage><PortfolioAnalysis /></DashboardPage></Route>
      <Route path="/risk-analysis"><DashboardPage><RiskAnalysis /></DashboardPage></Route>
      <Route path="/research"><DashboardPage><Research /></DashboardPage></Route>
      <Route path="/watchlists"><DashboardPage><Watchlists /></DashboardPage></Route>
      <Route path="/monte-carlo"><DashboardPage><MonteCarlo /></DashboardPage></Route>
      <Route><Redirect to="/" /></Route>
    </Switch>
  );
}
