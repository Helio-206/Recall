import type { VideoNote, VideoNoteUpsert } from "@recall/shared";

import { apiFetch } from "@/lib/api";

export function getVideoNote(token: string, videoId: string) {
  return apiFetch<VideoNote | null>(`/videos/${videoId}/notes`, { token });
}

export function upsertVideoNote(token: string, videoId: string, payload: VideoNoteUpsert) {
  return apiFetch<VideoNote | null>(`/videos/${videoId}/notes`, {
    token,
    method: "PUT",
    body: JSON.stringify(payload),
  });
}