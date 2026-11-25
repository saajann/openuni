import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-base font-semibold whitespace-nowrap cursor-pointer transition-colors disabled:cursor-not-allowed disabled:bg-border disabled:text-muted-foreground",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary-hover active:scale-[0.98]",
        outline: "border border-input bg-transparent text-foreground hover:bg-surface-raised",
        ghost: "text-muted-foreground hover:bg-surface-raised hover:text-foreground",
      },
      size: {
        default: "px-6 py-3",
        sm: "px-3 py-1.5 text-sm",
      },
      block: {
        true: "w-full",
        false: "",
      },
    },
    defaultVariants: { variant: "default", size: "default", block: false },
  },
);

type ButtonProps = React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean };

function Button({ className, variant, size, block, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, block }), className)}
      {...props}
    />
  );
}

export { Button, buttonVariants };
