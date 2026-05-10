"use client";

import { AlertCircle, BrainCircuit, Clock3, HelpCircle, Lightbulb, Loader2, RefreshCw } from "lucide-react";

import type { AISummaryJob, RecallVideo, VideoLearningInsights } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn, formatTimestamp } from "@/lib/utils";

type LearningIntelligencePanelProps = {
  video: RecallVideo | null;
  insights: VideoLearningInsights | null;
  job: AISummaryJob | null;
  state: "idle" | "loading" | "processing" | "completed" | "failed";
  error: string | null;
  message: string;
  isWorking: boolean;
  onGenerate: (options?: { force?: boolean }) => Promise<void> | void;
  onSeek: (seconds: number) => void;
};

type LearningNotesPanelProps = Omit<LearningIntelligencePanelProps, "onSeek">;

const phaseProgress: Record<string, number> = {
  queued: 10,
  chunking_transcript: 24,
  summarizing_chunks: 48,
  calling_ai_provider: 62,
  extracting_concepts: 72,
  structuring_summary: 88,
  retrying: 18,
  completed: 100,
  failed: 100,
};

export function LearningIntelligencePanel({
  video,
  insights,
  job,
  state,
  error,
  message,
  isWorking,
  onGenerate,
  onSeek,
}: LearningIntelligencePanelProps) {
  const canGenerate = video?.transcript_status === "completed";
  const phase = job?.payload.phase || job?.status || insights?.status || "pending";
  const progress =
    state === "completed"
      ? 100
      : state === "failed"
        ? 100
        : (phaseProgress[phase] ?? (isWorking ? 40 : 0));

  if (!video) {
    return (
      <PanelState
        icon={<BrainCircuit className="size-5" />}
        title="No video selected"
        body="Choose a video to open its AI learning summary."
      />
    );
  }

  if (state === "loading") {
    return (
      <PanelState
        icon={<Loader2 className="size-5 animate-spin" />}
        title="Loading AI insights..."
        body="Checking the latest learning analysis for this video."
      />
    );
  }

  if (state === "processing") {
    return (
      <div className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
        <div className="flex items-start gap-3">
          <Loader2 className="mt-0.5 size-4 animate-spin text-primary" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground">{message}</p>
            <p className="mt-1 text-xs leading-5 text-muted">
              Recall is turning the transcript into a structured study layer.
            </p>
          </div>
        </div>
        <Progress value={progress} className="mt-5" />
      </div>
    );
  }

  if (state === "failed") {
    return (
      <PanelState
        icon={<AlertCircle className="size-5" />}
        title="AI analysis failed. Try again."
        body={error || "The worker could not build the AI learning summary."}
        action={
          <Button type="button" variant="secondary" onClick={() => void onGenerate({ force: true })}>
            <RefreshCw />
            Retry
          </Button>
        }
      />
    );
  }

  if (!canGenerate) {
    return (
      <PanelState
        icon={<Clock3 className="size-5" />}
        title="AI insights are waiting on the transcript"
        body="Finish transcript generation first, then Recall can extract concepts, questions, and important moments."
      />
    );
  }

  if (!insights?.summary) {
    return (
      <PanelState
        icon={<BrainCircuit className="size-5" />}
        title="AI insights are not available yet."
        body="Generate a structured summary, key concepts, study questions, and important moments from this transcript."
        action={
          <Button type="button" onClick={() => void onGenerate()}>
            Generate AI Summary
          </Button>
        }
      />
    );
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-lg border border-primary/20 bg-primary/5 p-5 shadow-insetPanel">
        <div className="flex items-center gap-2 text-primary">
          <BrainCircuit className="size-4" />
          <h2 className="font-heading text-base font-semibold text-foreground">Short Summary</h2>
        </div>
        <p className="mt-3 text-sm leading-7 text-foreground/90">{insights.summary.short_summary}</p>
      </section>

      <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
        <h3 className="font-heading text-base font-semibold text-foreground">Detailed Summary</h3>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-foreground/85">
          {insights.summary.detailed_summary}
        </p>
      </section>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center gap-2">
            <Lightbulb className="size-4 text-primary" />
            <h3 className="font-heading text-base font-semibold text-foreground">Key Concepts</h3>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {insights.key_concepts.map((concept) => (
              <span
                key={concept.id}
                className="rounded-full border border-border bg-background/70 px-3 py-1 text-xs text-foreground"
              >
                {concept.concept}
                <span className="ml-1 text-muted">{Math.round(concept.relevance_score * 100)}%</span>
              </span>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center gap-2">
            <Lightbulb className="size-4 text-primary" />
            <h3 className="font-heading text-base font-semibold text-foreground">Key Takeaways</h3>
          </div>
          <ul className="mt-4 grid gap-3">
            {insights.key_takeaways.map((takeaway) => (
              <li key={takeaway.id} className="rounded-md border border-border bg-background/55 px-3 py-2 text-sm leading-6 text-foreground/85">
                {takeaway.content}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center gap-2">
            <HelpCircle className="size-4 text-primary" />
            <h3 className="font-heading text-base font-semibold text-foreground">Review Questions</h3>
          </div>
          <div className="mt-4 grid gap-3">
            {insights.review_questions.map((question) => (
              <article key={question.id} className="rounded-md border border-border bg-background/55 p-4">
                <p className="text-sm font-medium text-foreground">{question.question}</p>
                <p className="mt-2 text-sm leading-6 text-muted">{question.answer}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center gap-2">
            <Clock3 className="size-4 text-primary" />
            <h3 className="font-heading text-base font-semibold text-foreground">Important Moments</h3>
          </div>
          <div className="mt-4 grid gap-2">
            {insights.important_moments.map((moment) => (
              <button
                key={moment.id}
                type="button"
                onClick={() => onSeek(moment.timestamp)}
                className="rounded-md border border-border bg-background/55 p-3 text-left transition-colors hover:border-primary/40 hover:bg-primary/5"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-foreground">{moment.title}</span>
                  <span className="font-mono text-xs text-primary">{formatTimestamp(moment.timestamp)}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-muted">{moment.description}</p>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export function LearningNotesPanel({
  video,
  insights,
  state,
  error,
  message,
  isWorking,
  onGenerate,
}: LearningNotesPanelProps) {
  if (!video) {
    return (
      <PanelState
        icon={<BrainCircuit className="size-5" />}
        title="No video selected"
        body="Choose a video to open its notes."
      />
    );
  }

  if (state === "loading" || state === "processing") {
    return (
      <PanelState
        icon={<Loader2 className={cn("size-5", isWorking ? "animate-spin" : "")} />}
        title={message}
        body="The notes view will be ready as soon as the AI summary completes."
      />
    );
  }

  if (state === "failed") {
    return (
      <PanelState
        icon={<AlertCircle className="size-5" />}
        title="AI analysis failed. Try again."
        body={error || "The notes could not be generated."}
        action={
          <Button type="button" variant="secondary" onClick={() => void onGenerate({ force: true })}>
            <RefreshCw />
            Retry
          </Button>
        }
      />
    );
  }

  if (!insights?.summary?.learning_notes) {
    return (
      <PanelState
        icon={<Lightbulb className="size-5" />}
        title="Notes are not available yet."
        body="AI notes are generated from the transcript once the summary finishes."
        action={
          video.transcript_status === "completed" ? (
            <Button type="button" onClick={() => void onGenerate()}>
              Generate Notes
            </Button>
          ) : undefined
        }
      />
    );
  }

  return (
    <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-heading text-lg font-semibold text-foreground">Study Notes</h2>
          <p className="mt-1 text-sm text-muted">Auto-generated notes you can use as a quick review sheet.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => void onGenerate({ force: true })}>
          <RefreshCw />
          Regenerate
        </Button>
      </div>
      <div className="mt-5 whitespace-pre-wrap rounded-md border border-border bg-background/55 p-4 text-sm leading-7 text-foreground/90">
        {insights.summary.learning_notes}
      </div>
    </section>
  );
}

function PanelState({
  icon,
  title,
  body,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="grid min-h-[320px] place-items-center rounded-lg border border-border bg-surface/80 p-6 text-center shadow-insetPanel">
      <div>
        <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
          {icon}
        </div>
        <h3 className="mt-4 font-heading text-base font-semibold text-foreground">{title}</h3>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">{body}</p>
        {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
      </div>
    </div>
  );
}