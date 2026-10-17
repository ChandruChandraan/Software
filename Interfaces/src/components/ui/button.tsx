import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "destructive" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon" | "xs";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white disabled:pointer-events-none disabled:opacity-40 select-none",
          // Variants
          variant === "default" &&
            "bg-white text-black hover:bg-zinc-200 active:bg-zinc-300 font-semibold shadow-sm",
          variant === "secondary" &&
            "bg-zinc-900 text-white border border-zinc-800 hover:bg-zinc-800 hover:border-zinc-700",
          variant === "outline" &&
            "border border-zinc-700 bg-transparent text-zinc-100 hover:bg-zinc-900 hover:text-white hover:border-zinc-500",
          variant === "destructive" &&
            "bg-zinc-900 text-red-400 border border-red-950/80 hover:bg-red-950/40 hover:text-red-300 hover:border-red-800",
          variant === "ghost" &&
            "text-zinc-400 hover:text-white hover:bg-zinc-900",
          variant === "link" &&
            "text-white underline-offset-4 hover:underline",
          // Sizes
          size === "default" && "h-9 px-4 py-2",
          size === "xs" && "h-6 px-2 text-xs rounded",
          size === "sm" && "h-8 rounded-md px-3 text-xs",
          size === "lg" && "h-10 rounded-md px-8 text-base",
          size === "icon" && "h-9 w-9",
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
