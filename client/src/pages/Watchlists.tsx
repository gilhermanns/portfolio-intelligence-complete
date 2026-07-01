import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { Plus, Trash2, Eye } from "lucide-react";
 
export default function Watchlists() {
  const { toast } = useToast();
  const [newListName, setNewListName] = useState("");
  const [newTicker, setNewTicker] = useState<Record<number, string>>({});
  const [selected, setSelected] = useState<number | null>(null);
 
  const listQuery = trpc.watchlist.list.useQuery();
  const watchlists = listQuery.data ?? [];
  const activeId = selected ?? watchlists[0]?.id;
 
  const itemsQuery = trpc.watchlist.getItems.useQuery({ watchlistId: activeId! }, { enabled: !!activeId });
  const quotesQuery = trpc.market.getBatchQuotes.useQuery(
    { tickers: (itemsQuery.data ?? []).map((i) => i.ticker) },
    { enabled: (itemsQuery.data?.length ?? 0) > 0, refetchInterval: 30_000 }
  );
 
  const createList = trpc.watchlist.create.useMutation({ onSuccess: () => { listQuery.refetch(); setNewListName(""); toast({ type: "success", title: "Watchlist created" }); } });
  const deleteList = trpc.watchlist.delete.useMutation({ onSuccess: () => { listQuery.refetch(); toast({ type: "success", title: "Watchlist deleted" }); } });
  const addItem = trpc.watchlist.addItem.useMutation({ onSuccess: () => { itemsQuery.refetch(); setNewTicker({}); toast({ type: "success", title: "Ticker added" }); } });
  const removeItem = trpc.watchlist.removeItem.useMutation({ onSuccess: () => itemsQuery.refetch() });
 
  const quotesMap = Object.fromEntries((quotesQuery.data ?? []).map((q) => [q.ticker, q]));
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">Watchlists</h1><p className="text-muted-foreground mt-1">Track tickers across asset classes</p></div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Eye className="h-4 w-4 text-accent" />Your Lists</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {watchlists.map((wl) => (
              <div key={wl.id} onClick={() => setSelected(wl.id)} className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-colors ${activeId === wl.id ? "bg-accent/15 text-accent" : "hover:bg-muted/50 text-muted-foreground"}`}>
                <span className="text-sm font-medium">{wl.name}</span>
                <button onClick={(e) => { e.stopPropagation(); deleteList.mutate({ watchlistId: wl.id }); }} className="text-muted-foreground hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
              </div>
            ))}
            <div className="flex gap-2 mt-3">
              <Input placeholder="New list name…" value={newListName} onChange={(e) => setNewListName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && newListName && createList.mutate({ name: newListName })} className="text-sm" />
              <Button size="icon" onClick={() => newListName && createList.mutate({ name: newListName })}><Plus className="h-4 w-4" /></Button>
            </div>
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{watchlists.find((w) => w.id === activeId)?.name ?? "Select a list"}</CardTitle>
              {activeId && (
                <div className="flex gap-2">
                  <Input placeholder="Add ticker…" value={newTicker[activeId] ?? ""} onChange={(e) => setNewTicker((p) => ({ ...p, [activeId]: e.target.value.toUpperCase() }))} onKeyDown={(e) => { if (e.key === "Enter" && newTicker[activeId]) addItem.mutate({ watchlistId: activeId, ticker: newTicker[activeId] }); }} className="w-32 text-sm" />
                  <Button size="sm" onClick={() => newTicker[activeId] && addItem.mutate({ watchlistId: activeId, ticker: newTicker[activeId] })}><Plus className="h-4 w-4" /></Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {(itemsQuery.data ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No tickers yet — add one above.</p>
            ) : (
              <div className="space-y-2">
                {(itemsQuery.data ?? []).map((item) => {
                  const q = quotesMap[item.ticker];
                  return (
                    <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
                      <div><p className="text-sm font-medium text-foreground">{item.ticker}</p><p className="text-xs text-muted-foreground">{item.assetClass}</p></div>
                      <div className="flex items-center gap-4">
                        {q && <div className="text-right"><p className="text-sm font-medium text-foreground">${q.price.toFixed(2)}</p><p className={`text-xs ${q.changePct >= 0 ? "text-green-400" : "text-red-400"}`}>{q.changePct >= 0 ? "+" : ""}{q.changePct.toFixed(2)}%</p></div>}
                        <button onClick={() => removeItem.mutate({ watchlistItemId: item.id })} className="text-muted-foreground hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
