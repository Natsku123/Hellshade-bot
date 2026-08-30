import * as React from "react";

import { cn } from "@/lib/utils";

function Badge({
  className,
  variant = "default",
  ...props
}: React.ComponentProps<"span"> & {
  variant?: "default" | "secondary" | "outline";
}) {
  const variants = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    outline: "text-foreground border",
  } as const;

  return (
    <span
      data-slot="badge"
      className={cn(
        "inline-flex items-center rounded-md border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}

export { Badge };
