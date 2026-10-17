import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "white" | "success" | "warning";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-1 focus:ring-white select-none",
        variant === "default" &&
          "border-zinc-800 bg-zinc-900 text-zinc-100",
        variant === "white" &&
          "border-white bg-white text-black font-bold",
        variant === "secondary" &&
          "border-zinc-800 bg-zinc-900 text-zinc-300",
        variant === "destructive" &&
          "border-zinc-800 bg-zinc-950 text-zinc-300",
        variant === "outline" &&
          "border-zinc-700 text-zinc-200",
        variant === "success" &&
          "border-zinc-700 bg-zinc-900 text-white",
        variant === "warning" &&
          "border-zinc-700 bg-zinc-900 text-zinc-200",
        className
      )}
      {...props}
    />
  );
}

export { Badge };
