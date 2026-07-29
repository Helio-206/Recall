"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useRef } from "react";
import { motion } from "framer-motion";
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
  const activeIndex = useMemo(() => {
    if (typeof activeTimestamp !== "number") return -1;
    return blocks.findIndex(
      (block) => activeTimestamp >= block.startTime && activeTimestamp <= block.endTime + 4,
    );
  }, [activeTimestamp, blocks]);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const blockRefs = useRef<Array<HTMLDivElement | null>>([]);
  const phase = job?.payload.phase || job?.status || video?.transcript_status || "pending";
  const progress =
    state === "completed" || state === "failed"
      ? 100
      : (phaseProgress[phase] ?? (isWorking ? 44 : 0));

  useEffect(() => {
    const container = scrollRef.current;
    const activeBlock = blockRefs.current[activeIndex];
    if (!container || !activeBlock || activeIndex < 0) return;

    const targetTop =
      activeBlock.offsetTop - container.clientHeight * 0.32 + activeBlock.clientHeight / 2;
    container.scrollTo({ top: Math.max(0, targetTop), behavior: "smooth" });
  }, [activeIndex]);

  return (
    <section className="border-t border-border/70 pt-5">
      <header className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="size-4 text-primary" />
            <h2 className="font-heading text-base font-semibold text-foreground">Transcript</h2>
          </div>
          <p className="mt-1 text-xs text-muted">
            {video ? "Follows playback automatically" : "No lesson selected"}
          </p>
        </div>
        <StatusPill state={state} transcriptStatus={video?.transcript_status} />
      </header>

      {!video ? (
        <PanelState
          icon={<FileText className="size-5" />}
          title="No lesson selected"
          body="Choose a curriculum item to open its transcript."
        />
      ) : state === "loading" ? (
        <PanelState
          icon={<Loader2 className="size-5 animate-spin" />}
          title="Loading transcript"
          body="Opening the latest learning document."
        />
      ) : state === "processing" ? (
        <div className="grid min-h-[380px] place-items-center py-8">
          <div className="w-full max-w-xl border border-border bg-surface p-5">
            <div className="flex items-start gap-3">
              <Loader2 className="mt-0.5 size-4 animate-spin text-primary" />
              <div>
                <p className="text-sm font-medium text-foreground">{message}</p>
                <p className="mt-1 text-xs leading-5 text-muted">
                  The learning document will appear here when processing is complete.
                </p>
              </div>
            </div>
            <Progress value={progress} className="mt-5 h-1" />
          </div>
        </div>
      ) : state === "failed" ? (
        <PanelState
          icon={<AlertCircle className="size-5" />}
          title="Transcript generation failed"
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
        <div
          ref={scrollRef}
          className="thin-scrollbar mt-5 max-h-[620px] min-h-[420px] overflow-y-auto pr-2"
        >
          <article className="mx-auto max-w-2xl pb-20">
            {blocks.map((block, index) => {
              const isActive = index === activeIndex;
              return (
                <motion.div
                  key={`${block.startTime}-${index}`}
                  data-transcript-block
                  data-active={isActive ? "true" : "false"}
                  ref={(node) => {
                    blockRefs.current[index] = node;
                  }}
                  initial={false}
                  animate={{
                    backgroundColor: isActive ? "rgba(79, 124, 255, 0.10)" : "rgba(0, 0, 0, 0)",
                  }}
                  transition={{ duration: 0.25 }}
                  className={cn(
                    "group grid grid-cols-[58px_minmax(0,1fr)] border-l-2 px-3 py-3 sm:grid-cols-[72px_minmax(0,1fr)] sm:px-4",
                    isActive ? "border-primary" : "border-transparent",
                  )}
                >
                  <button
                    type="button"
                    onClick={() => onSeek?.(block.startTime)}
                    className={cn(
                      "h-fit pt-1 text-left font-mono text-xs transition-colors",
                      isActive ? "font-semibold text-primary" : "text-muted hover:text-foreground",
                    )}
                    aria-label={`Seek to ${formatTimestamp(block.startTime)}`}
                  >
                    {formatTimestamp(block.startTime)}
                  </button>
                  <button
                    type="button"
                    onClick={() => onSeek?.(block.startTime)}
                    className="text-left text-[15px] leading-7 text-foreground/90 sm:text-base sm:leading-7"
                  >
                    {block.text}
                  </button>
                </motion.div>
              );
            })}
          </article>
        </div>
      ) : (
        <PanelState
          icon={<FileText className="size-5" />}
          title="This lesson has no transcript yet"
          body="Generate a complete, timestamped learning document from the video."
          action={
            <Button type="button" onClick={() => void generate()}>
              Generate Transcript
            </Button>
          }
        />
      )}
    </section>
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
    const endsSentence = /[.!?]["')\]]?$/.test(currentText.trim());
    const shouldBreak = currentText.length > 360 && endsSentence;
    const isTooLong = next.length > 620;
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
      className: "border-success/30 bg-success/10 text-success",
      icon: CheckCircle2,
    },
    failed: {
      label: "Failed",
      className: "border-red-500/30 bg-red-500/10 text-red-200",
      icon: AlertCircle,
    },
    processing: {
      label: "Working",
      className: "border-primary/30 bg-primary/10 text-blue-100",
      icon: Loader2,
    },
    loading: {
      label: "Loading",
      className: "border-primary/30 bg-primary/10 text-blue-100",
      icon: Loader2,
    },
    pending: {
      label: "Pending",
      className: "border-border bg-white/[0.03] text-muted",
      icon: Clock3,
    },
    idle: {
      label: "Empty",
      className: "border-border bg-white/[0.03] text-muted",
      icon: Clock3,
    },
  }[resolvedState];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex h-7 items-center gap-1.5 rounded border px-2 text-xs font-medium",
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
    <div className="grid min-h-[420px] place-items-center p-6 text-center">
      <div>
        <div className="mx-auto grid size-11 place-items-center rounded border border-border bg-surface text-primary">
          {icon}
        </div>
        <h3 className="mt-4 font-heading text-base font-semibold text-foreground">{title}</h3>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted">{body}</p>
        {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
      </div>
    </div>
  );
}
