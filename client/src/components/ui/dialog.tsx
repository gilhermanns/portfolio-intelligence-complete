import { createContext, useContext, useState, ReactNode, useEffect } from "react";
interface Ctx { open: boolean; setOpen: (v: boolean) => void; }
const DialogContext = createContext<Ctx>({ open: false, setOpen: () => {} });
export function Dialog({ children }: { children: ReactNode }) { const [open, setOpen] = useState(false); return <DialogContext.Provider value={{ open, setOpen }}>{children}</DialogContext.Provider>; }
export function DialogTrigger({ children, asChild }: { children: ReactNode; asChild?: boolean }) {
  const { setOpen } = useContext(DialogContext);
  if (asChild && children && typeof children === "object" && "props" in (children as any)) { const child = children as React.ReactElement; return <child.type {...child.props} onClick={() => setOpen(true)} />; }
  return <span onClick={() => setOpen(true)}>{children}</span>;
}
export function DialogContent({ children, className="" }: { children: ReactNode; className?: string }) {
  const { open, setOpen } = useContext(DialogContext);
  useEffect(() => { const h = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); }; document.addEventListener("keydown", h); return () => document.removeEventListener("keydown", h); }, [setOpen]);
  if (!open) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center"><div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} /><div className={`relative z-10 bg-card border border-border rounded-lg p-6 w-full max-w-md shadow-2xl ${className}`}><button onClick={() => setOpen(false)} className="absolute top-4 right-4 text-muted-foreground hover:text-foreground">✕</button>{children}</div></div>;
}
export function DialogHeader({ children }: { children: ReactNode }) { return <div className="mb-4">{children}</div>; }
export function DialogTitle({ children }: { children: ReactNode }) { return <h2 className="text-lg font-semibold text-foreground">{children}</h2>; }
