import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide uppercase",
  {
    variants: {
      variant: {
        default: "border border-border bg-surface-raised text-muted-foreground",
        exam: "bg-cal-exam/15 text-cal-exam",
        deadline: "bg-cal-deadline/15 text-cal-deadline",
        holiday: "bg-cal-holiday/15 text-cal-holiday",
        event: "bg-cal-event/15 text-cal-event",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span data-slot="badge" className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
