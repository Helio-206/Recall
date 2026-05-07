import type { IngestionAccepted, IngestionJob } from "@recall/shared";

import { apiFetch } from "@/lib/api";

export type IngestUrlPayload = {
  url: string;
  title?: string;
};

export function ingestUrl(token: string, spaceId: string, payload: IngestUrlPayload) {
  return apiFetch<IngestionAccepted>(`/spaces/${spaceId}/ingest`, {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getIngestionJob(token: string, jobId: string) {
  return apiFetch<IngestionJob>(`/ingestion/jobs/${jobId}`, { token });
}
