import type {
  SearchQuery,
  SearchQueryCreate,
  SearchResponse,
  SearchResultClickPayload,
} from "@recall/shared";

import { apiFetch } from "@/lib/api";

type SearchParams = {
  q: string;
  kind?: string;
  spaceId?: string;
  page?: number;
  per_page?: number;
};

export function searchLearningContent(token: string, params: SearchParams) {
  const searchParams = new URLSearchParams();
  searchParams.set("q", params.q);
  if (params.kind && params.kind !== "all") searchParams.set("kind", params.kind);
  if (params.spaceId) searchParams.set("space_id", params.spaceId);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));
  return apiFetch<SearchResponse>(`/search?${searchParams.toString()}`, { token });
}

export function getRecentSearches(token: string) {
  return apiFetch<SearchQuery[]>("/search/recent", { token });
}

export function saveRecentSearch(token: string, payload: SearchQueryCreate) {
  return apiFetch<SearchQuery>("/search/recent", {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function recordSearchClick(token: string, payload: SearchResultClickPayload) {
  return apiFetch<{ id: string }>("/search/clicks", {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}