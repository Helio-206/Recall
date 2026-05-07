"use client";

import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

import type { IngestionJob } from "@recall/shared";
import { Progress } from "@/components/ui/progress";

type IngestionStatusProps = {
  state: "idle" | "validating" | "processing" | "completed" | "failed";
  message: string;
  job: IngestionJob | null;
};

export function IngestionStatus({ state, message, job }: IngestionStatusProps) {
  if (state === "idle") return null;

  const detectedCount = job?.payload.detected_count ?? 0;
  const addedCount = job?.payload.added_count ?? 0;
  const duplicateCount = job?.payload.duplicate_count ?? 0;
  const skippedCount = job?.payload.skipped_count ?? 0;
  const progress =
    state === "completed"
      ? 100
      : state === "failed"
        ? 100
        : detectedCount > 0
          ? Math.max(35, Math.min(90, Math.round((addedCount / detectedCount) * 100)))
          : state === "validating"
            ? 18
            : 56;

  return (
    <div className="rounded-lg border border-border bg-background/70 p-4 shadow-insetPanel">
      <div className="flex items-start gap-3">
        <StatusIcon state={state} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{message}</p>
          {job?.payload.source_type === "playlist" && (
            <p className="mt-1 text-xs text-muted">
              {detectedCount} detected · {addedCount} added
              {duplicateCount ? ` · ${duplicateCount} duplicates` : ""}
              {skippedCount ? ` · ${skippedCount} unavailable` : ""}
            </p>
          )}
        </div>
      </div>
      <Progress value={progress} className="mt-4" />
    </div>
  );
}

function StatusIcon({ state }: { state: IngestionStatusProps["state"] }) {
  if (state === "completed") {
    return <CheckCircle2 className="mt-0.5 size-4 text-success" />;
  }
  if (state === "failed") {
    return <AlertCircle className="mt-0.5 size-4 text-red-300" />;
  }
  return <Loader2 className="mt-0.5 size-4 animate-spin text-primary" />;
}
