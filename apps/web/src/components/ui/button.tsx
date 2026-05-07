import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 ease-premium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/70 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-white shadow-[0_10px_30px_rgba(47,107,255,0.28)] hover:bg-primary/90",
        secondary:
          "border border-border bg-surface-2 text-foreground shadow-insetPanel hover:border-primary/40 hover:bg-white/[0.06]",
        ghost: "text-muted hover:bg-white/[0.06] hover:text-foreground",
        warm: "bg-warm text-background hover:bg-warm/90",
        danger: "border border-red-500/30 bg-red-500/10 text-red-200 hover:bg-red-500/15",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-5",
        icon: "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
