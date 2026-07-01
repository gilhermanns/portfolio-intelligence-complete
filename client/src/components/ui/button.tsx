import { ButtonHTMLAttributes, forwardRef } from "react";
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { variant?: "default"|"outline"|"ghost"|"destructive"; size?: "sm"|"md"|"lg"|"icon"; }
const V: Record<string,string> = { default:"bg-primary text-primary-foreground hover:bg-primary/90", outline:"border border-border bg-transparent hover:bg-muted text-foreground", ghost:"bg-transparent hover:bg-muted text-foreground", destructive:"bg-destructive text-destructive-foreground hover:bg-destructive/90" };
const S: Record<string,string> = { sm:"h-8 px-3 text-xs", md:"h-9 px-4 text-sm", lg:"h-10 px-6 text-sm", icon:"h-9 w-9" };
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ className="", variant="default", size="md", ...props }, ref) => (
  <button ref={ref} className={`inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50 disabled:pointer-events-none ${V[variant]} ${S[size]} ${className}`} {...props} />
));
Button.displayName = "Button";
