import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
 
export default function MarketIntelligence() {
  const query = trpc.market.getLatestIntelligence.useQuery();
  const items = query.data ?? [];
 
  if (query.isLoading) return <div className="space-y-4">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-48" />)}</div>;
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">Market Intelligence</h1><p className="text-muted-foreground mt-1">Weekly macro overview across asset classes</p></div>
      <div className="space-y-4">
        {items.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{item.assetClass}</CardTitle>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Week of {item.weekOf}</span>
                  <Badge variant={item.sentiment === "bullish" ? "success" : item.sentiment === "bearish" ? "destructive" : "warning"}>{item.sentiment}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground leading-relaxed">{item.summary}</p>
              <div>
                <p className="text-xs font-medium text-foreground mb-2">Key Drivers</p>
                <div className="flex flex-wrap gap-2">{item.keyDrivers.map((d) => <span key={d} className="text-xs px-2.5 py-1 rounded-full bg-muted text-muted-foreground">{d}</span>)}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
