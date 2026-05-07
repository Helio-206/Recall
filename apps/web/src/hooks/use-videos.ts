"use client";

import { useCallback, useState } from "react";

import type { RecallVideo } from "@recall/shared";
import { getSpaceVideos } from "@/lib/api/videos";

export function useVideos(token: string | null, spaceId: string | null) {
  const [videos, setVideos] = useState<RecallVideo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token || !spaceId) return [];
    setIsLoading(true);
    setError(null);
    try {
      const nextVideos = await getSpaceVideos(token, spaceId);
      setVideos(nextVideos);
      return nextVideos;
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Unable to load videos.";
      setError(message);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [spaceId, token]);

  return { videos, isLoading, error, refresh };
}
