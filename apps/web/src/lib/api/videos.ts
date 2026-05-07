import type { RecallVideo } from "@recall/shared";

import { apiFetch } from "@/lib/api";

export function getSpaceVideos(token: string, spaceId: string) {
  return apiFetch<RecallVideo[]>(`/spaces/${spaceId}/videos`, { token });
}
