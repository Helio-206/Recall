"use client";

import { Clock3, Lightbulb, Loader2, Save } from "lucide-react";

import type { RecallVideo, VideoLearningInsights, VideoNote } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useVideoNote } from "@/hooks/use-video-note";
import { formatTimestamp } from "@/lib/utils";

type VideoNotesPanelProps = {
  video: RecallVideo | null;
  token: string | null;
  currentTimestamp: number;
  insights: VideoLearningInsights | null;
  onSeek: (seconds: number) => void;
};

export function VideoNotesPanel({
  video,
  token,
  currentTimestamp,
  insights,
  onSeek,
}: VideoNotesPanelProps) {
  const noteState = useVideoNote({ token, videoId: video?.id ?? null });

  if (!video) {
    return <PanelState title="No video selected" body="Choose a video to open your notes." />;
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="font-heading text-lg font-semibold text-foreground">Personal Notes</h2>
            <p className="mt-1 text-sm text-muted">
              Write your own study notes and anchor them to a precise video timestamp.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => noteState.setAnchorTimestamp(Math.floor(currentTimestamp))}
            >
              <Clock3 />
              Use current time {formatTimestamp(currentTimestamp)}
            </Button>
            <Button type="button" onClick={() => void noteState.save()} disabled={!noteState.isDirty || noteState.isSaving}>
              {noteState.isSaving ? <Loader2 className="animate-spin" /> : <Save />}
              Save note
            </Button>
          </div>
        </div>

        <div className="mt-5 grid gap-4">
          <div className="grid gap-2">
            <label className="text-xs font-medium uppercase tracking-[0.18em] text-muted">Title</label>
            <Input
              value={noteState.title}
              onChange={(event) => noteState.setTitle(event.target.value)}
              placeholder="Example: Aperture cheat sheet"
              maxLength={180}
            />
          </div>

          <div className="grid gap-2">
            <label className="text-xs font-medium uppercase tracking-[0.18em] text-muted">Content</label>
            <Textarea
              value={noteState.content}
              onChange={(event) => noteState.setContent(event.target.value)}
              placeholder="Capture the explanation in your own words, plus the part you want to revisit later."
              className="min-h-[220px]"
              maxLength={12000}
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            {typeof noteState.anchorTimestamp === "number" ? (
              <button
                type="button"
                onClick={() => onSeek(noteState.anchorTimestamp ?? 0)}
                className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-primary"
              >
                Jump to {formatTimestamp(noteState.anchorTimestamp)}
              </button>
            ) : (
              <span className="rounded-full border border-border bg-background/70 px-3 py-1 text-muted">
                No timestamp anchor yet
              </span>
            )}

            {noteState.note?.updated_at ? (
              <span className="text-muted">Last saved at {new Date(noteState.note.updated_at).toLocaleString()}</span>
            ) : null}

            {noteState.error ? <span className="text-red-300">{noteState.error}</span> : null}
            {!noteState.error && noteState.isDirty ? <span className="text-muted">Unsaved changes</span> : null}
            {!noteState.error && !noteState.isDirty && noteState.note ? <span className="text-success">Saved</span> : null}
          </div>
        </div>
      </section>

      <AINotesSection insights={insights} onSeek={onSeek} note={noteState.note} />
    </div>
  );
}

function AINotesSection({
  insights,
  onSeek,
  note,
}: {
  insights: VideoLearningInsights | null;
  onSeek: (seconds: number) => void;
  note: VideoNote | null;
}) {
  if (!insights?.summary?.learning_notes) {
    return (
      <PanelState
        title="AI notes are not available yet."
        body={
          note
            ? "Your personal note is saved. AI notes will appear here once the summary finishes."
            : "Generate the AI summary to unlock automatic study notes alongside your own notes."
        }
      />
    );
  }

  return (
    <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
      <div className="flex items-center gap-2">
        <Lightbulb className="size-4 text-primary" />
        <h3 className="font-heading text-base font-semibold text-foreground">AI Notes</h3>
      </div>
      <p className="mt-1 text-sm text-muted">Use the generated notes as a companion sheet while refining your own notes above.</p>
      <div className="mt-5 whitespace-pre-wrap rounded-md border border-border bg-background/55 p-4 text-sm leading-7 text-foreground/90">
        {insights.summary.learning_notes}
      </div>

      {insights.important_moments.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {insights.important_moments.slice(0, 4).map((moment) => (
            <button
              key={moment.id}
              type="button"
              onClick={() => onSeek(moment.timestamp)}
              className="rounded-full border border-border bg-background/70 px-3 py-1 text-xs text-muted transition-colors hover:border-primary/35 hover:text-foreground"
            >
              {moment.title} · {formatTimestamp(moment.timestamp)}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function PanelState({ title, body }: { title: string; body: string }) {
  return (
    <div className="grid min-h-[260px] place-items-center rounded-lg border border-border bg-surface/80 p-6 text-center shadow-insetPanel">
      <div>
        <h3 className="font-heading text-base font-semibold text-foreground">{title}</h3>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">{body}</p>
      </div>
    </div>
  );
}