"use client";

import { useCallback, useEffect, useState } from "react";

import type { VideoNote } from "@recall/shared";
import { getVideoNote, upsertVideoNote } from "@/lib/api/notes";

type UseVideoNoteOptions = {
  token: string | null;
  videoId: string | null;
};

export function useVideoNote({ token, videoId }: UseVideoNoteOptions) {
  const [note, setNote] = useState<VideoNote | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [anchorTimestamp, setAnchorTimestamp] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  const reset = useCallback((nextNote: VideoNote | null) => {
    setNote(nextNote);
    setTitle(nextNote?.title ?? "");
    setContent(nextNote?.content ?? "");
    setAnchorTimestamp(nextNote?.anchor_timestamp ?? null);
    setIsDirty(false);
  }, []);

  const refresh = useCallback(async () => {
    if (!token || !videoId) {
      reset(null);
      return null;
    }
    setIsLoading(true);
    setError(null);
    try {
      const nextNote = await getVideoNote(token, videoId);
      reset(nextNote);
      return nextNote;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load notes.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [reset, token, videoId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function save() {
    if (!token || !videoId) return null;
    setIsSaving(true);
    setError(null);
    try {
      const nextNote = await upsertVideoNote(token, videoId, {
        title: title || null,
        content,
        anchor_timestamp: anchorTimestamp,
      });
      reset(nextNote);
      return nextNote;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save note.");
      return null;
    } finally {
      setIsSaving(false);
    }
  }

  return {
    note,
    title,
    content,
    anchorTimestamp,
    isSaving,
    isLoading,
    isDirty,
    error,
    setTitle: (value: string) => {
      setTitle(value);
      setIsDirty(true);
    },
    setContent: (value: string) => {
      setContent(value);
      setIsDirty(true);
    },
    setAnchorTimestamp: (value: number | null) => {
      setAnchorTimestamp(value);
      setIsDirty(true);
    },
    save,
    refresh,
  };
}