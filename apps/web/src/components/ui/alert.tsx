import * as React from "react";

import { cn } from "@/lib/utils";

function Alert({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      role="alert"
      data-slot="alert"
      className={cn(
        "rounded-md border border-destructive bg-destructive/10 p-4 text-center text-destructive-foreground",
        className,
      )}
      {...props}
    />
  );
}

export { Alert };
