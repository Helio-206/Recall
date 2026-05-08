"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { AISummaryJob, VideoLearningInsights } from "@recall/shared";
import { createAISummaryJob, getAISummaryJob, getVideoAISummary } from "@/lib/api/ai-summaries";

type AIUiState = "idle" | "loading" | "processing" | "completed" | "failed";

type UseAISummaryOptions = {
  token: string | null;
  videoId: string | null;
};

const phaseMessages: Record<string, string> = {
  queued: "Analyzing transcript...",
  chunking_transcript: "Analyzing transcript...",
  summarizing_chunks: "Generating learning insights...",
  extracting_concepts: "Extracting key concepts...",
  structuring_summary: "Structuring educational summary...",
  retrying: "Retrying AI analysis...",
  completed: "AI summary ready.",
  failed: "AI analysis failed. Try again.",
};

const queuedJobTimeoutMs = 30_000;

export function useAISummary({ token, videoId }: UseAISummaryOptions) {
  const [insights, setInsights] = useState<VideoLearningInsights | null>(null);
  const [job, setJob] = useState<AISummaryJob | null>(null);
  const [state, setState] = useState<AIUiState>("idle");
  const [error, setError] = useState<string | null>(null);
  const pollingJobId = useRef<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token || !videoId) {
      setInsights(null);
      setJob(null);
      setState("idle");
      return null;
    }

    setState((current) => (current === "processing" ? current : "loading"));
    setError(null);
    try {
      const nextInsights = await getVideoAISummary(token, videoId);
      setInsights(nextInsights);
      setJob(nextInsights.job);

      if (nextInsights.status === "completed" && nextInsights.summary) {
        setState("completed");
      } else if (nextInsights.status === "failed") {
        setState("failed");
        setError(nextInsights.error_message || "AI analysis failed. Try again.");
      } else if (
        nextInsights.job?.status === "pending" ||
        nextInsights.job?.status === "processing"
      ) {
        pollingJobId.current = nextInsights.job.id;
        setState("processing");
      } else {
        setState("idle");
      }
      return nextInsights;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load AI insights.");
      setState("failed");
      return null;
    }
  }, [token, videoId]);

  const generate = useCallback(
    async ({ force = false }: { force?: boolean } = {}) => {
      if (!token || !videoId) return;
      setError(null);
      setState("processing");
      try {
        const nextJob = await createAISummaryJob(token, videoId, { force });
        if (nextJob.status === "completed") {
          pollingJobId.current = null;
          setJob(nextJob);
          await refresh();
          return;
        }
        pollingJobId.current = nextJob.id;
        setJob(nextJob);
      } catch (requestError) {
        setError(
          requestError instanceof Error ? requestError.message : "Unable to start AI analysis.",
        );
        setState("failed");
      }
    },
    [token, videoId],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!token || !pollingJobId.current || state !== "processing") return undefined;

    let isActive = true;
    const poll = async () => {
      if (!pollingJobId.current) return;
      try {
        const nextJob = await getAISummaryJob(token, pollingJobId.current);
        if (!isActive) return;
        setJob(nextJob);

        const jobAge = Date.now() - new Date(nextJob.created_at).getTime();
        if (nextJob.status === "pending" && nextJob.attempts === 0 && jobAge > queuedJobTimeoutMs) {
          setError("The AI summary worker looks offline. Start it and try again.");
          setState("failed");
          pollingJobId.current = null;
          return;
        }

        if (nextJob.status === "completed") {
          pollingJobId.current = null;
          await refresh();
          return;
        }

        if (nextJob.status === "failed") {
          pollingJobId.current = null;
          setError(nextJob.error_message || "AI analysis failed. Try again.");
          setState("failed");
          await refresh();
        }
      } catch (requestError) {
        if (!isActive) return;
        pollingJobId.current = null;
        setError(
          requestError instanceof Error ? requestError.message : "Unable to check AI summary status.",
        );
        setState("failed");
      }
    };

    void poll();
    const interval = window.setInterval(() => void poll(), 3000);
    return () => {
      isActive = false;
      window.clearInterval(interval);
    };
  }, [refresh, state, token]);

  const message = useMemo(() => {
    if (error) return error;
    const phase = job?.payload.phase || job?.status || insights?.status;
    if (phase && phaseMessages[phase]) return phaseMessages[phase];
    if (state === "loading") return "Loading AI insights...";
    return "AI insights are not available yet.";
  }, [error, insights?.status, job, state]);

  return {
    insights,
    summary: insights?.summary ?? null,
    job,
    state,
    error,
    message,
    isWorking: state === "processing" || state === "loading",
    refresh,
    generate,
  };
}