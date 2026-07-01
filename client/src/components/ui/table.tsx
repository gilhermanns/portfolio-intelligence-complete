import { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";
export function Table({ className="", ...props }: HTMLAttributes<HTMLTableElement>) { return <div className="w-full overflow-auto"><table className={`w-full caption-bottom text-sm ${className}`} {...props} /></div>; }
export function TableHeader(p: HTMLAttributes<HTMLTableSectionElement>) { return <thead {...p} />; }
export function TableBody(p: HTMLAttributes<HTMLTableSectionElement>) { return <tbody {...p} />; }
export function TableRow({ className="", ...p }: HTMLAttributes<HTMLTableRowElement>) { return <tr className={`border-b border-border/50 transition-colors hover:bg-muted/30 ${className}`} {...p} />; }
export function TableHead({ className="", ...p }: ThHTMLAttributes<HTMLTableCellElement>) { return <th className={`h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground ${className}`} {...p} />; }
export function TableCell({ className="", ...p }: TdHTMLAttributes<HTMLTableCellElement>) { return <td className={`px-4 py-2 align-middle text-sm ${className}`} {...p} />; }
