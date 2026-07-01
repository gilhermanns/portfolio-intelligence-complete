import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";
type ToastType = "success"|"error"|"warning"|"info";
interface Toast { id: string; type: ToastType; title: string; description?: string; }
interface ToastContextType { toast: (opts: Omit<Toast,"id">) => void; }
const ToastContext = createContext<ToastContextType>({ toast: () => {} });
export function useToast() { return useContext(ToastContext); }
const icons = { success: CheckCircle, error: XCircle, warning: AlertTriangle, info: Info };
const colors = { success:"text-green-400 bg-green-400/10 border-green-400/20", error:"text-red-400 bg-red-400/10 border-red-400/20", warning:"text-yellow-400 bg-yellow-400/10 border-yellow-400/20", info:"text-accent bg-accent/10 border-accent/20" };
function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const Icon = icons[toast.type];
  return <div className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg bg-card ${colors[toast.type]}`} style={{ animation:"slideIn 0.2s ease" }}><Icon className="h-5 w-5 flex-shrink-0 mt-0.5" /><div className="flex-1"><p className="text-sm font-medium text-foreground">{toast.title}</p>{toast.description && <p className="text-xs text-muted-foreground mt-0.5">{toast.description}</p>}</div><button onClick={onRemove} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button></div>;
}
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toast = useCallback((opts: Omit<Toast,"id">) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((p) => [...p, { id, ...opts }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
  }, []);
  return <ToastContext.Provider value={{ toast }}>{children}<div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 w-80">{toasts.map((t) => <ToastItem key={t.id} toast={t} onRemove={() => setToasts((p) => p.filter((x) => x.id !== t.id))} />)}</div></ToastContext.Provider>;
}
