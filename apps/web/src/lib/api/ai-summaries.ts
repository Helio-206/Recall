import type { AISummaryJob, VideoLearningInsights } from "@recall/shared";

import { apiFetch } from "@/lib/api";

export function getVideoAISummary(token: string, videoId: string) {
  return apiFetch<VideoLearningInsights>(`/videos/${videoId}/ai-summary`, { token });
}

export function createAISummaryJob(
  token: string,
  videoId: string,
  payload: { force?: boolean } = {},
) {
  return apiFetch<AISummaryJob>(`/videos/${videoId}/ai-summary/jobs`, {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAISummaryJob(token: string, jobId: string) {
  return apiFetch<AISummaryJob>(`/ai-summaries/jobs/${jobId}`, { token });
}