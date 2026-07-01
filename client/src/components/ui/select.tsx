import { SelectHTMLAttributes, forwardRef } from "react";
import { ChevronDown } from "lucide-react";
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(({ className="", children, ...props }, ref) => (
  <div className="relative">
    <select ref={ref} className={`flex h-9 w-full appearance-none rounded-md border border-border bg-input px-3 pr-8 py-1 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50 ${className}`} {...props}>{children}</select>
    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
  </div>
));
Select.displayName = "Select";
