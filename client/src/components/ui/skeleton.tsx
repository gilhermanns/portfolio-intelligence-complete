import { HTMLAttributes } from "react";
export function Skeleton({ className="", ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`animate-pulse rounded-md bg-muted/60 ${className}`} {...props} />; }
export function SkeletonCard() { return <div className="rounded-lg border border-border bg-card p-6 space-y-3"><Skeleton className="h-4 w-1/3" /><Skeleton className="h-8 w-1/2" /><Skeleton className="h-3 w-2/3" /></div>; }
