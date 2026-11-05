import * as React from "react";

import { cn } from "@/lib/utils";
import { fieldClasses } from "@/components/ui/input";

// shortcut: native <select> (no Radix popover), fine until a design needs custom option rendering.
function Select({ className, ...props }: React.ComponentProps<"select">) {
  return <select data-slot="select" className={cn(fieldClasses, className)} {...props} />;
}

export { Select };
