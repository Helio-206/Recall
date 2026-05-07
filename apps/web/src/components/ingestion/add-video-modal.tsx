"use client";

import { FormEvent, type ReactNode, useCallback, useEffect, useState } from "react";
import { LinkIcon, Plus } from "lucide-react";

import type { RecallSpace } from "@recall/shared";
import { IngestionStatus } from "@/components/ingestion/ingestion-status";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useIngestion } from "@/hooks/use-ingestion";
import { useAuthStore } from "@/stores/auth-store";
import { useSpaceStore } from "@/stores/space-store";

type AddVideoModalProps = {
  spaces: RecallSpace[];
  spaceId?: string;
  trigger?: ReactNode;
};

export function AddVideoModal({ spaces, spaceId, trigger }: AddVideoModalProps) {
  const token = useAuthStore((state) => state.token);
  const fetchSpace = useSpaceStore((state) => state.fetchSpace);
  const fetchSpaces = useSpaceStore((state) => state.fetchSpaces);
  const [open, setOpen] = useState(false);
  const [selectedSpaceId, setSelectedSpaceId] = useState(spaceId || spaces[0]?.id || "");
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const handleCompleted = useCallback(async () => {
    if (!token || !selectedSpaceId) return;
    await fetchSpace(token, selectedSpaceId);
    await fetchSpaces(token);
  }, [fetchSpace, fetchSpaces, selectedSpaceId, token]);
  const ingestion = useIngestion({
    token,
    spaceId: selectedSpaceId || null,
    onCompleted: handleCompleted,
  });
  const ingestionState = ingestion.state;
  const resetIngestion = ingestion.reset;

  useEffect(() => {
    if (spaceId) {
      setSelectedSpaceId(spaceId);
      return;
    }
    if (!selectedSpaceId && spaces[0]?.id) {
      setSelectedSpaceId(spaces[0].id);
    }
  }, [selectedSpaceId, spaceId, spaces]);

  useEffect(() => {
    if (ingestionState === "completed") {
      const timeout = window.setTimeout(() => {
        setUrl("");
        setTitle("");
        setOpen(false);
        resetIngestion();
      }, 900);
      return () => window.clearTimeout(timeout);
    }
    return undefined;
  }, [ingestionState, resetIngestion]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedSpaceId) return;
    await ingestion.submit({ url, title: title || undefined });
  }

  function onOpenChange(nextOpen: boolean) {
    setOpen(nextOpen);
    if (!nextOpen && !ingestion.isWorking) {
      ingestion.reset();
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus />
            Add Content
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add YouTube Source</DialogTitle>
          <DialogDescription>
            Paste a video or playlist URL. Recall will extract metadata without downloading files.
          </DialogDescription>
        </DialogHeader>
        <form className="grid gap-4" onSubmit={onSubmit}>
          {!spaceId && (
            <div className="grid gap-2">
              <Label htmlFor="space-select">Space</Label>
              <select
                id="space-select"
                className="h-11 rounded-md border border-border bg-background/70 px-3 text-sm text-foreground outline-none focus:border-primary/70 focus:ring-2 focus:ring-primary/20"
                value={selectedSpaceId}
                onChange={(event) => setSelectedSpaceId(event.target.value)}
                disabled={ingestion.isWorking}
                required
              >
                {spaces.map((space) => (
                  <option key={space.id} value={space.id}>
                    {space.title}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="grid gap-2">
            <Label htmlFor="video-url">YouTube URL</Label>
            <div className="relative">
              <LinkIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
              <Input
                id="video-url"
                type="url"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                className="pl-10"
                placeholder="https://www.youtube.com/watch?v=..."
                disabled={ingestion.isWorking}
                required
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="video-title">Title Override</Label>
            <Input
              id="video-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Optional for single videos"
              disabled={ingestion.isWorking}
            />
          </div>

          <IngestionStatus
            state={ingestion.state}
            message={ingestion.statusMessage}
            job={ingestion.job}
          />

          <Button type="submit" disabled={ingestion.isWorking || !spaces.length}>
            {ingestion.isWorking ? "Processing" : "Extract Metadata"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
