import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";
 
export default function Research() {
  const query = trpc.research.getReports.useQuery();
  const reports = query.data ?? [];
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">Research Reports</h1><p className="text-muted-foreground mt-1">Your saved analyses and weekly memos</p></div>
      {reports.length === 0 ? (
        <Card><CardContent className="py-16 text-center"><FileText className="h-10 w-10 text-muted-foreground mx-auto mb-3" /><p className="text-muted-foreground">No reports yet. Use the AI Assistant to generate analyses.</p></CardContent></Card>
      ) : (
        <div className="space-y-4">
          {reports.map((r) => (
            <Card key={r.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <CardTitle className="text-base leading-snug">{r.title}</CardTitle>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge variant="outline">{r.type.replace("_"," ")}</Badge>
                    <span className="text-xs text-muted-foreground">{new Date(r.generatedAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose-dark text-sm line-clamp-4 text-muted-foreground" dangerouslySetInnerHTML={{ __html: r.content.replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>").replace(/\n/g,"<br/>").slice(0,600) + "…" }} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
