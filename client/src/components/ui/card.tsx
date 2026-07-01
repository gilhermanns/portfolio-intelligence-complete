import { HTMLAttributes } from "react";
export function Card({ className="", ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`rounded-lg border border-border bg-card text-card-foreground ${className}`} {...props} />; }
export function CardHeader({ className="", ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`flex flex-col space-y-1 p-6 ${className}`} {...props} />; }
export function CardTitle({ className="", ...props }: HTMLAttributes<HTMLHeadingElement>) { return <h3 className={`text-lg font-semibold leading-none tracking-tight text-foreground ${className}`} {...props} />; }
export function CardDescription({ className="", ...props }: HTMLAttributes<HTMLParagraphElement>) { return <p className={`text-sm text-muted-foreground ${className}`} {...props} />; }
export function CardContent({ className="", ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`p-6 pt-0 ${className}`} {...props} />; }
export function CardFooter({ className="", ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`flex items-center p-6 pt-0 ${className}`} {...props} />; }
