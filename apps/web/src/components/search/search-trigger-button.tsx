"use client";

import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { openGlobalSearch } from "./global-search-modal";

export function SearchTriggerButton({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  return (
    <Button
      type="button"
      variant="secondary"
      className={cn(compact ? "h-10 px-3" : "justify-between", className)}
      onClick={() => openGlobalSearch()}
    >
      <span className="flex items-center gap-2">
        <Search />
        {!compact ? "Search your knowledge" : null}
      </span>
      {!compact ? <span className="font-mono text-xs text-muted">Ctrl K</span> : null}
    </Button>
  );
}