"use client";

import { Shield } from "lucide-react";
import { Badge } from "@/components/ui/badge";

/**
 * Visual indicator that this is a read-only dashboard
 */
export function ReadOnlyBadge() {
  return (
    <Badge variant="outline" className="gap-1">
      <Shield className="size-3" />
      Read-only
    </Badge>
  );
}

/**
 * Footer disclaimer for read-only mode
 */
export function ReadOnlyDisclaimer() {
  return (
    <div className="text-xs text-muted-foreground">
      <p>
        This is a <strong>read-only</strong> dashboard. Data displayed is from{" "}
        <strong>Hellshade-bot</strong> and cannot be modified through this interface.
      </p>
    </div>
  );
}
