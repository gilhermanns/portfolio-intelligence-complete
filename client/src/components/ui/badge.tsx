import { HTMLAttributes } from "react";
interface BadgeProps extends HTMLAttributes<HTMLSpanElement> { variant?: "default"|"success"|"warning"|"destructive"|"outline"; }
const V: Record<string,string> = { default:"bg-accent/20 text-accent", success:"bg-green-500/20 text-green-400", warning:"bg-yellow-500/20 text-yellow-400", destructive:"bg-destructive/20 text-red-400", outline:"border border-border text-muted-foreground" };
export function Badge({ className="", variant="default", ...props }: BadgeProps) { return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${V[variant]} ${className}`} {...props} />; }
