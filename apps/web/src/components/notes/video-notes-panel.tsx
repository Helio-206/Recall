"use client";

import { Clock3, Loader2, Save } from "lucide-react";

import type { RecallVideo } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useVideoNote } from "@/hooks/use-video-note";
import { formatTimestamp } from "@/lib/utils";

type VideoNotesPanelProps = {
  video: RecallVideo | null;
  token: string | null;
  currentTimestamp: number;
  onSeek: (seconds: number) => void;
};

export function VideoNotesPanel({ video, token, currentTimestamp, onSeek }: VideoNotesPanelProps) {
  const noteState = useVideoNote({ token, videoId: video?.id ?? null });

  if (!video) {
    return <PanelState title="No video selected" body="Choose a video to open your notes." />;
  }

  return (
    <section className="border-t border-border/70 pt-5">
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
          <Button
            type="button"
            onClick={() => void noteState.save()}
            disabled={!noteState.isDirty || noteState.isSaving}
          >
            {noteState.isSaving ? <Loader2 className="animate-spin" /> : <Save />}
            Save note
          </Button>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="grid gap-2">
          <label className="text-xs font-medium text-muted">Title</label>
          <Input
            value={noteState.title}
            onChange={(event) => noteState.setTitle(event.target.value)}
            placeholder="Example: Aperture cheat sheet"
            maxLength={180}
          />
        </div>

        <div className="grid gap-2">
          <label className="text-xs font-medium text-muted">Content</label>
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
              className="rounded border border-primary/30 bg-primary/10 px-3 py-1 text-primary"
            >
              Jump to {formatTimestamp(noteState.anchorTimestamp)}
            </button>
          ) : (
            <span className="rounded border border-border bg-background/70 px-3 py-1 text-muted">
              No timestamp anchor yet
            </span>
          )}

          {noteState.note?.updated_at ? (
            <span className="text-muted">
              Last saved at {new Date(noteState.note.updated_at).toLocaleString()}
            </span>
          ) : null}

          {noteState.error ? <span className="text-red-300">{noteState.error}</span> : null}
          {!noteState.error && noteState.isDirty ? (
            <span className="text-muted">Unsaved changes</span>
          ) : null}
          {!noteState.error && !noteState.isDirty && noteState.note ? (
            <span className="text-success">Saved</span>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function PanelState({ title, body }: { title: string; body: string }) {
  return (
    <div className="grid min-h-[260px] place-items-center border-t border-border/70 p-6 text-center">
      <div>
        <h3 className="font-heading text-base font-semibold text-foreground">{title}</h3>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">{body}</p>
      </div>
    </div>
  );
}
