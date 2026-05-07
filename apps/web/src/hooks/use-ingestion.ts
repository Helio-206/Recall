"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { IngestionJob } from "@recall/shared";
import { getIngestionJob, ingestUrl } from "@/lib/api/ingestion";

type IngestionUiState = "idle" | "validating" | "processing" | "completed" | "failed";

type UseIngestionOptions = {
  token: string | null;
  spaceId: string | null;
  onCompleted?: (job: IngestionJob) => void | Promise<void>;
};

const phaseMessages: Record<string, string> = {
  queued: "Reading source...",
  reading_source: "Reading source...",
  extracting_metadata: "Extracting metadata...",
  structuring_curriculum: "Structuring curriculum...",
  adding_videos: "Adding videos to your Learning Space...",
  retrying: "Retrying metadata extraction...",
  completed: "Added videos to your Learning Space.",
  failed: "We could not process that source.",
};

const queuedJobTimeoutMs = 90_000;

export function useIngestion({ token, spaceId, onCompleted }: UseIngestionOptions) {
  const [state, setState] = useState<IngestionUiState>("idle");
  const [job, setJob] = useState<IngestionJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingJobId = useRef<string | null>(null);

  const statusMessage = useMemo(() => {
    if (error) return error;
    if (!job) return "Paste a YouTube link to start building this learning path.";
    const phase = job.payload.phase || job.status;
    if (phaseMessages[phase]) return phaseMessages[phase];
    if (job.status === "processing") return "Structuring curriculum...";
    return "Adding videos to your Learning Space...";
  }, [error, job]);

  const submit = useCallback(
    async ({ url, title }: { url: string; title?: string }) => {
      if (!token || !spaceId) return;
      setState("validating");
      setError(null);
      setJob(null);
      try {
        const accepted = await ingestUrl(token, spaceId, { url, title });
        pollingJobId.current = accepted.job_id;
        setState("processing");
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Unable to start ingestion.");
        setState("failed");
      }
    },
    [spaceId, token],
  );

  const reset = useCallback(() => {
    pollingJobId.current = null;
    setState("idle");
    setJob(null);
    setError(null);
  }, []);

  useEffect(() => {
    if (!token || !pollingJobId.current || state !== "processing") return undefined;

    let isActive = true;
    const poll = async () => {
      if (!pollingJobId.current) return;
      try {
        const nextJob = await getIngestionJob(token, pollingJobId.current);
        if (!isActive) return;
        setJob(nextJob);
        const jobAge = Date.now() - new Date(nextJob.created_at).getTime();
        if (
          nextJob.status === "pending" &&
          nextJob.attempts === 0 &&
          jobAge > queuedJobTimeoutMs
        ) {
          pollingJobId.current = null;
          setError("The metadata worker looks offline. Start it and try again.");
          setState("failed");
          return;
        }
        if (nextJob.status === "completed") {
          pollingJobId.current = null;
          setState("completed");
          await onCompleted?.(nextJob);
          return;
        }
        if (nextJob.status === "failed") {
          pollingJobId.current = null;
          setError(nextJob.error_message || "We could not process that YouTube source.");
          setState("failed");
        }
      } catch (requestError) {
        if (!isActive) return;
        pollingJobId.current = null;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "We could not check ingestion status.",
        );
        setState("failed");
      }
    };

    void poll();
    const interval = window.setInterval(() => void poll(), 1800);
    return () => {
      isActive = false;
      window.clearInterval(interval);
    };
  }, [onCompleted, state, token]);

  return {
    state,
    job,
    error,
    statusMessage,
    isWorking: state === "validating" || state === "processing",
    submit,
    reset,
  };
}
