"use client";

import type { ReactNode } from "react";
import { useMemo } from "react";
import { AlertCircle, CheckCircle2, Clock3, FileText, Loader2, RefreshCw } from "lucide-react";

import type { RecallVideo, TranscriptSegment } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useTranscript } from "@/hooks/use-transcript";
import { cn, formatTimestamp } from "@/lib/utils";

type TranscriptPanelProps = {
  video: RecallVideo | null;
  token: string | null;
  onCompleted?: () => void | Promise<void>;
  activeTimestamp?: number | null;
  onSeek?: (seconds: number) => void;
};

const phaseProgress: Record<string, number> = {
  queued: 10,
  fetching_captions: 36,
  preparing_audio: 24,
  generating_transcript: 52,
  structuring_transcript: 78,
  finalizing_document: 92,
  retrying: 18,
  completed: 100,
  failed: 100,
};

export function TranscriptPanel({
  video,
  token,
  onCompleted,
  activeTimestamp,
  onSeek,
}: TranscriptPanelProps) {
  const { segments, job, state, error, message, generate, isWorking } = useTranscript({
    token,
    videoId: video?.id ?? null,
    onCompleted,
  });

  const blocks = useMemo(() => buildTranscriptBlocks(segments), [segments]);
  const phase = job?.payload.phase || job?.status || video?.transcript_status || "pending";
  const progress =
    state === "completed"
      ? 100
      : state === "failed"
        ? 100
        : (phaseProgress[phase] ?? (isWorking ? 44 : 0));

  return (
    <aside className="flex min-h-[520px] flex-col rounded-lg border border-border bg-surface/85 shadow-insetPanel 2xl:sticky 2xl:top-8 2xl:h-[calc(100vh-4rem)]">
      <header className="border-b border-border p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <FileText className="size-4 text-primary" />
              <h2 className="font-heading text-base font-semibold text-foreground">Transcript</h2>
            </div>
            <p className="mt-1 truncate text-xs text-muted">
              {video ? "Interactive learning document" : "No video selected"}
            </p>
          </div>
          <StatusPill state={state} transcriptStatus={video?.transcript_status} />
        </div>
      </header>

      {!video ? (
        <PanelState
          icon={<FileText className="size-5" />}
          title="No video selected"
          body="Choose a curriculum item to open its transcript."
        />
      ) : state === "loading" ? (
        <PanelState
          icon={<Loader2 className="size-5 animate-spin" />}
          title="Loading transcript..."
          body="Checking the latest learning document."
        />
      ) : state === "processing" ? (
        <div className="grid flex-1 place-items-center p-5">
          <div className="w-full rounded-lg border border-border bg-background/65 p-5">
            <div className="flex items-start gap-3">
              <Loader2 className="mt-0.5 size-4 animate-spin text-primary" />
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">{message}</p>
                <p className="mt-1 text-xs leading-5 text-muted">
                  Recall is turning this source into a complete learning document.
                </p>
              </div>
            </div>
            <Progress value={progress} className="mt-5" />
          </div>
        </div>
      ) : state === "failed" ? (
        <PanelState
          icon={<AlertCircle className="size-5" />}
          title="Transcript generation failed. Try again."
          body={error || "The worker could not generate this transcript."}
          action={
            <Button
              type="button"
              variant="secondary"
              onClick={() => void generate({ force: true })}
            >
              <RefreshCw />
              Retry
            </Button>
          }
        />
      ) : blocks.length > 0 ? (
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <article className="grid gap-3">
            {blocks.map((block, index) => {
              const isActive =
                typeof activeTimestamp === "number" &&
                activeTimestamp >= block.startTime &&
                activeTimestamp <= block.endTime + 4;

              return (
                <button
                  key={`${index}-${block.startTime}`}
                  type="button"
                  onClick={() => onSeek?.(block.startTime)}
                  className={cn(
                    "rounded-md border p-3 text-left transition-colors",
                    onSeek ? "hover:border-primary/40 hover:bg-primary/5" : "cursor-default",
                    isActive ? "border-primary/50 bg-primary/10" : "border-border bg-background/45",
                  )}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-xs text-primary">{formatTimestamp(block.startTime)}</span>
                    <span className="text-[11px] uppercase tracking-[0.18em] text-muted">Section</span>
                  </div>
                  <p className="mt-2 text-sm leading-7 text-foreground/90">{block.text}</p>
                </button>
              );
            })}
          </article>
        </div>
      ) : (
        <PanelState
          icon={<FileText className="size-5" />}
          title="This video has no transcript yet."
          body="Generate a complete text document from the video audio."
          action={
            <Button type="button" onClick={() => void generate()}>
              Generate Transcript
            </Button>
          }
        />
      )}
    </aside>
  );
}

function buildTranscriptBlocks(segments: TranscriptSegment[]) {
  const blocks: Array<{ startTime: number; endTime: number; text: string }> = [];
  let currentText = "";
  let currentStart = 0;
  let currentEnd = 0;

  for (const segment of segments) {
    const text = segment.text.trim();
    if (!text) continue;

    if (!currentText) {
      currentText = text;
      currentStart = segment.start_time;
      currentEnd = segment.end_time;
      continue;
    }

    const next = `${currentText} ${text}`;
    const shouldBreak = currentText.length > 420 && /[.!?]["')\]]?$/.test(currentText.trim());
    const isTooLong = next.length > 720;
    const jumped = segment.start_time - currentEnd > 25;

    if (shouldBreak || isTooLong || jumped) {
      blocks.push({ startTime: currentStart, endTime: currentEnd, text: currentText });
      currentText = text;
      currentStart = segment.start_time;
      currentEnd = segment.end_time;
      continue;
    }

    currentText = next;
    currentEnd = segment.end_time;
  }

  if (currentText) {
    blocks.push({ startTime: currentStart, endTime: currentEnd, text: currentText });
  }

  return blocks;
}

function StatusPill({
  state,
  transcriptStatus,
}: {
  state: "idle" | "loading" | "processing" | "completed" | "failed";
  transcriptStatus?: RecallVideo["transcript_status"];
}) {
  const resolvedState = state === "idle" && transcriptStatus ? transcriptStatus : state;
  const config = {
    completed: {
      label: "Ready",
      className: "border-success/35 bg-success/10 text-success",
      icon: CheckCircle2,
    },
    failed: {
      label: "Failed",
      className: "border-red-500/35 bg-red-500/10 text-red-200",
      icon: AlertCircle,
    },
    processing: {
      label: "Working",
      className: "border-primary/35 bg-primary/10 text-blue-100",
      icon: Loader2,
    },
    loading: {
      label: "Loading",
      className: "border-primary/35 bg-primary/10 text-blue-100",
      icon: Loader2,
    },
    pending: {
      label: "Pending",
      className: "border-border bg-white/[0.04] text-muted",
      icon: Clock3,
    },
    idle: {
      label: "Empty",
      className: "border-border bg-white/[0.04] text-muted",
      icon: Clock3,
    },
  }[resolvedState];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex h-7 shrink-0 items-center gap-1.5 rounded-md border px-2 text-xs font-medium",
        config.className,
      )}
    >
      <Icon
        className={cn(
          "size-3.5",
          resolvedState === "processing" || resolvedState === "loading" ? "animate-spin" : "",
        )}
      />
      {config.label}
    </span>
  );
}

function PanelState({
  icon,
  title,
  body,
  action,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="grid flex-1 place-items-center p-6 text-center">
      <div>
        <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
          {icon}
        </div>
        <h3 className="mt-4 font-heading text-base font-semibold text-foreground">{title}</h3>
        <p className="mx-auto mt-2 max-w-xs text-sm leading-6 text-muted">{body}</p>
        {action && <div className="mt-5 flex justify-center">{action}</div>}
      </div>
    </div>
  );
}
