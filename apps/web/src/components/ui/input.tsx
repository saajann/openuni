import * as React from "react";

import { cn } from "@/lib/utils";

export const fieldClasses =
  "w-full rounded-md border border-input bg-surface-raised px-4 py-3 text-base text-foreground placeholder:text-muted-foreground focus-visible:border-primary disabled:cursor-not-allowed disabled:opacity-60";

function Input({ className, type = "text", ...props }: React.ComponentProps<"input">) {
  return <input type={type} data-slot="input" className={cn(fieldClasses, className)} {...props} />;
}

export { Input };
