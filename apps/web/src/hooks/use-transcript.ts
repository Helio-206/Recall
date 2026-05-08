"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { TranscriptJob, VideoTranscript } from "@recall/shared";
import { createTranscriptJob, getTranscriptJob, getVideoTranscript } from "@/lib/api/transcripts";

type TranscriptUiState = "idle" | "loading" | "processing" | "completed" | "failed";

type UseTranscriptOptions = {
  token: string | null;
  videoId: string | null;
  onCompleted?: () => void | Promise<void>;
};

const phaseMessages: Record<string, string> = {
  queued: "Preparing audio...",
  fetching_captions: "Reading YouTube captions...",
  preparing_audio: "Preparing audio...",
  generating_transcript: "Generating transcript...",
  structuring_transcript: "Structuring transcript...",
  finalizing_document: "Finalizing learning document...",
  retrying: "Retrying transcript generation...",
  completed: "Transcript ready.",
  failed: "Transcript generation failed. Try again.",
};

const queuedJobTimeoutMs = 120_000;

export function useTranscript({ token, videoId, onCompleted }: UseTranscriptOptions) {
  const [transcript, setTranscript] = useState<VideoTranscript | null>(null);
  const [job, setJob] = useState<TranscriptJob | null>(null);
  const [state, setState] = useState<TranscriptUiState>("idle");
  const [error, setError] = useState<string | null>(null);
  const pollingJobId = useRef<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token || !videoId) {
      setTranscript(null);
      setJob(null);
      setState("idle");
      return null;
    }

    setState((current) => (current === "processing" ? current : "loading"));
    setError(null);
    try {
      const nextTranscript = await getVideoTranscript(token, videoId);
      setTranscript(nextTranscript);
      setJob(nextTranscript.job);
      if (nextTranscript.status === "completed") {
        setState("completed");
      } else if (nextTranscript.status === "failed") {
        setState("failed");
        setError(nextTranscript.error_message || "Transcript generation failed. Try again.");
      } else if (
        nextTranscript.job?.status === "pending" ||
        nextTranscript.job?.status === "processing"
      ) {
        pollingJobId.current = nextTranscript.job.id;
        setState("processing");
      } else {
        setState("idle");
      }
      return nextTranscript;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load transcript.");
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
        const nextJob = await createTranscriptJob(token, videoId, { force });
        pollingJobId.current = nextJob.id;
        setJob(nextJob);
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to start transcript generation.",
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
        const nextJob = await getTranscriptJob(token, pollingJobId.current);
        if (!isActive) return;
        setJob(nextJob);

        const jobAge = Date.now() - new Date(nextJob.created_at).getTime();
        if (nextJob.status === "pending" && nextJob.attempts === 0 && jobAge > queuedJobTimeoutMs) {
          setError("The transcript worker looks offline. Start it and try again.");
          setState("failed");
          pollingJobId.current = null;
          return;
        }

        if (nextJob.status === "completed") {
          pollingJobId.current = null;
          await refresh();
          await onCompleted?.();
          return;
        }

        if (nextJob.status === "failed") {
          pollingJobId.current = null;
          setError(nextJob.error_message || "Transcript generation failed. Try again.");
          setState("failed");
          await refresh();
        }
      } catch (requestError) {
        if (!isActive) return;
        pollingJobId.current = null;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to check transcript status.",
        );
        setState("failed");
      }
    };

    void poll();
    const interval = window.setInterval(() => void poll(), 2500);
    return () => {
      isActive = false;
      window.clearInterval(interval);
    };
  }, [onCompleted, refresh, state, token]);

  const message = useMemo(() => {
    if (error) return error;
    const phase = job?.payload.phase || job?.status || transcript?.status;
    if (phase && phaseMessages[phase]) return phaseMessages[phase];
    if (state === "loading") return "Loading transcript...";
    return "This video has no transcript yet.";
  }, [error, job, state, transcript?.status]);

  return {
    transcript,
    segments: transcript?.segments ?? [],
    job,
    state,
    error,
    message,
    isWorking: state === "processing" || state === "loading",
    refresh,
    generate,
  };
}
