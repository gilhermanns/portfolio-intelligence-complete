import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { MessageSquare, Send, RefreshCw } from "lucide-react";
 
const SUGGESTIONS = ["What is the impact of rising interest rates on equities?","Analyze the AI and semiconductor sector outlook","How should I position for a potential recession?","What are the risks of high portfolio concentration?"];
 
export default function ResearchAssistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const { toast } = useToast();
 
  const askMutation = trpc.research.ask.useMutation({
    onSuccess: (data) => { setAnswer(data.answer); toast({ type: "success", title: "Analysis complete" }); },
    onError: (e) => toast({ type: "error", title: "Error", description: e.message }),
  });
 
  const memoMutation = trpc.research.generateWeeklyMemo.useMutation({
    onSuccess: (data) => { setAnswer(`# ${data.title}\n\n${data.sections.map((s: any) => `## ${s.title}\n\n${s.content}`).join("\n\n")}`); toast({ type: "success", title: "Weekly memo generated" }); },
  });
 
  function handleAsk() { if (!question.trim()) return; askMutation.mutate({ question }); }
 
  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-foreground">AI Research Assistant</h1><p className="text-muted-foreground mt-1">Ask questions about markets, macro, and portfolio positioning</p></div>
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-2">
            <Input placeholder="e.g. What is the impact of rising rates on my portfolio?" value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleAsk()} />
            <Button onClick={handleAsk} disabled={askMutation.isPending || !question.trim()}>{askMutation.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => <button key={s} onClick={() => setQuestion(s)} className="text-xs px-3 py-1.5 rounded-full bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors">{s}</button>)}
          </div>
          <Button variant="outline" size="sm" onClick={() => memoMutation.mutate()} disabled={memoMutation.isPending}>
            {memoMutation.isPending ? <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Generating…</> : <><MessageSquare className="h-4 w-4 mr-2" />Generate Weekly
 
Memo</>}
          </Button>
        </CardContent>
      </Card>
      {answer && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><MessageSquare className="h-4 w-4 text-accent" />Analysis</CardTitle></CardHeader>
          <CardContent><div className="prose-dark" dangerouslySetInnerHTML={{ __html: answer.replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>").replace(/\*(.*?)\*/g,"<em>$1</em>").replace(/^## (.*)/gm,"<h2>$1</h2>").replace(/^# (.*)/gm,"<h2>$1</h2>").replace(/\n/g,"<br/>") }} /></CardContent>
        </Card>
      )}
    </div>
  );
}
