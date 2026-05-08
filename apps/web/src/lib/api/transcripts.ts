import type { TranscriptJob, VideoTranscript } from "@recall/shared";

import { apiFetch } from "@/lib/api";

export function getVideoTranscript(token: string, videoId: string) {
  return apiFetch<VideoTranscript>(`/videos/${videoId}/transcript`, { token });
}

export function createTranscriptJob(
  token: string,
  videoId: string,
  payload: { force?: boolean } = {},
) {
  return apiFetch<TranscriptJob>(`/videos/${videoId}/transcript/jobs`, {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTranscriptJob(token: string, jobId: string) {
  return apiFetch<TranscriptJob>(`/transcripts/jobs/${jobId}`, { token });
}
