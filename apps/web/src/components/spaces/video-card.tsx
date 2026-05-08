"use client";

import {
  AlertCircle,
  CheckCircle2,
  Circle,
  FileText,
  GripVertical,
  Loader2,
  Play,
  Timer,
} from "lucide-react";

import type { RecallVideo } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { cn, formatDuration } from "@/lib/utils";

type VideoCardProps = {
  video: RecallVideo;
  onToggle?: (video: RecallVideo) => void;
  onSelect?: (video: RecallVideo) => void;
  isUpdating?: boolean;
  isActive?: boolean;
  sequenceLabel?: string;
};

export function VideoCard({
  video,
  onToggle,
  onSelect,
  isUpdating = false,
  isActive = false,
  sequenceLabel,
}: VideoCardProps) {
  return (
    <article
      className={[
        "group grid grid-cols-[auto_1fr_auto] gap-4 rounded-lg border bg-surface/75 p-3 shadow-insetPanel transition-all duration-200 hover:border-primary/35 hover:bg-surface-2/80 sm:grid-cols-[auto_92px_1fr_auto]",
        isActive ? "border-primary/60 bg-surface-2" : "border-border",
      ].join(" ")}
    >
      <div className="hidden items-center text-muted/70 sm:flex">
        <GripVertical className="size-4" />
      </div>

      <button
        type="button"
        className="relative hidden aspect-video overflow-hidden rounded-md border border-border bg-background text-left outline-none transition-colors focus-visible:border-primary sm:block"
        onClick={() => onSelect?.(video)}
        aria-label={`Play ${video.title}`}
      >
        {video.thumbnail ? (
          <img src={video.thumbnail} alt="" className="h-full w-full object-cover opacity-90" />
        ) : (
          <div className="grid h-full w-full place-items-center bg-surface-2">
            <Play className="size-5 text-muted" />
          </div>
        )}
        <div className="absolute inset-0 bg-background/15" />
      </button>

      <button
        type="button"
        className="min-w-0 text-left outline-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-primary/60"
        onClick={() => onSelect?.(video)}
      >
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-muted">
            {sequenceLabel ?? String(video.order_index + 1).padStart(2, "0")}
          </span>
          <h3 className="truncate text-sm font-medium text-foreground">{video.title}</h3>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
          <span>{video.author || "Imported source"}</span>
          <span className="inline-flex items-center gap-1.5">
            <Timer className="size-3.5" />
            {formatDuration(video.duration)}
          </span>
          <TranscriptStatus status={video.transcript_status} />
        </div>
      </button>

      <Button
        type="button"
        variant={video.completed ? "secondary" : "ghost"}
        size="icon"
        className="self-center"
        disabled={isUpdating}
        aria-label={video.completed ? "Mark incomplete" : "Mark complete"}
        onClick={() => onToggle?.(video)}
      >
        {video.completed ? (
          <CheckCircle2 className="text-success" />
        ) : (
          <Circle className="text-muted" />
        )}
      </Button>
    </article>
  );
}

function TranscriptStatus({ status }: { status: RecallVideo["transcript_status"] }) {
  const config = {
    completed: {
      label: "Transcript",
      className: "text-success",
      icon: FileText,
    },
    processing: {
      label: "Transcribing",
      className: "text-primary",
      icon: Loader2,
    },
    failed: {
      label: "Transcript failed",
      className: "text-red-300",
      icon: AlertCircle,
    },
    pending: {
      label: "Transcript pending",
      className: "text-muted",
      icon: FileText,
    },
  }[status];
  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1.5", config.className)}>
      <Icon className={cn("size-3.5", status === "processing" ? "animate-spin" : "")} />
      {config.label}
    </span>
  );
}
