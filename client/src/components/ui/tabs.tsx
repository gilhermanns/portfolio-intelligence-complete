import { createContext, useContext, useState, ReactNode } from "react";
interface TabsCtx { value: string; setValue: (v: string) => void; }
const TabsContext = createContext<TabsCtx>({ value: "", setValue: () => {} });
export function Tabs({ children, defaultValue, value: cv, onValueChange }: { children: ReactNode; defaultValue?: string; value?: string; onValueChange?: (v: string) => void }) {
  const [iv, siv] = useState(defaultValue ?? "");
  const value = cv ?? iv;
  return <TabsContext.Provider value={{ value, setValue: (v) => { siv(v); onValueChange?.(v); } }}>{children}</TabsContext.Provider>;
}
export function TabsList({ children, className="" }: { children: ReactNode; className?: string }) { return <div className={`inline-flex items-center rounded-lg bg-muted p-1 gap-1 ${className}`}>{children}</div>; }
export function TabsTrigger({ value, children }: { value: string; children: ReactNode }) {
  const ctx = useContext(TabsContext);
  return <button onClick={() => ctx.setValue(value)} className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${ctx.value === value ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>{children}</button>;
}
export function TabsContent({ value, children, className="" }: { value: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (ctx.value !== value) return null;
  return <div className={className}>{children}</div>;
}
