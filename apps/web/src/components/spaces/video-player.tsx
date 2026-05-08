"use client";

import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from "react";
import { ExternalLink, Play } from "lucide-react";

import type { RecallVideo } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { formatDuration, getYouTubeEmbedUrl } from "@/lib/utils";

type VideoPlayerProps = {
  video?: RecallVideo | null;
  onTimeUpdate?: (time: number) => void;
};

export type VideoPlayerHandle = {
  seekTo: (seconds: number) => void;
};

type YouTubeInfoEvent = {
  event?: string;
  info?: {
    currentTime?: number;
  };
};

export const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(function VideoPlayer(
  { video, onTimeUpdate },
  ref,
) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const embedUrl = video ? getYouTubeEmbedUrl(video.url) : null;

  const postCommand = useCallback((func: string, args: unknown[] = []) => {
    iframeRef.current?.contentWindow?.postMessage(
      JSON.stringify({ event: "command", func, args }),
      "*",
    );
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      seekTo(seconds: number) {
        postCommand("seekTo", [Math.max(0, seconds), true]);
        onTimeUpdate?.(Math.max(0, seconds));
      },
    }),
    [onTimeUpdate, postCommand],
  );

  useEffect(() => {
    if (!embedUrl || !onTimeUpdate) return undefined;
    const notifyTimeUpdate = onTimeUpdate;

    function onMessage(event: MessageEvent) {
      if (!["https://www.youtube-nocookie.com", "https://www.youtube.com"].includes(event.origin)) {
        return;
      }

      let payload: YouTubeInfoEvent | null = null;
      if (typeof event.data === "string") {
        try {
          payload = JSON.parse(event.data) as YouTubeInfoEvent;
        } catch {
          return;
        }
      } else if (typeof event.data === "object" && event.data !== null) {
        payload = event.data as YouTubeInfoEvent;
      }

      if (payload?.event === "infoDelivery" && typeof payload.info?.currentTime === "number") {
        notifyTimeUpdate(payload.info.currentTime);
      }
    }

    window.addEventListener("message", onMessage);
    const interval = window.setInterval(() => postCommand("getCurrentTime"), 1000);

    return () => {
      window.removeEventListener("message", onMessage);
      window.clearInterval(interval);
    };
  }, [embedUrl, onTimeUpdate, postCommand]);

  if (!video) {
    return (
      <div className="grid aspect-video place-items-center rounded-lg border border-dashed border-border bg-surface/70 text-center shadow-insetPanel">
        <div>
          <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
            <Play className="size-5" />
          </div>
          <p className="mt-4 font-heading text-lg font-semibold text-foreground">
            No video selected
          </p>
          <p className="mt-2 text-sm text-muted">Add a video to start learning inside Recall.</p>
        </div>
      </div>
    );
  }

  return (
    <section className="overflow-hidden rounded-lg border border-border bg-black shadow-premium">
      <div className="relative aspect-video bg-black">
        {embedUrl ? (
          <iframe
            key={video.id}
            ref={iframeRef}
            src={embedUrl}
            title={video.title}
            className="absolute inset-0 h-full w-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerPolicy="strict-origin-when-cross-origin"
            allowFullScreen
          />
        ) : (
          <div className="absolute inset-0 grid place-items-center bg-background">
            <div className="text-center">
              <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-surface text-primary">
                <ExternalLink className="size-5" />
              </div>
              <p className="mt-4 text-sm text-muted">This source cannot be embedded.</p>
              <Button asChild className="mt-4" variant="secondary">
                <a href={video.url} target="_blank" rel="noreferrer">
                  Open Source
                  <ExternalLink />
                </a>
              </Button>
            </div>
          </div>
        )}
      </div>
      <div className="flex flex-col gap-3 border-t border-border bg-surface/95 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="truncate font-heading text-base font-semibold text-foreground">
            {video.title}
          </p>
          <p className="mt-1 text-xs text-muted">
            {video.author || "Imported source"} - {formatDuration(video.duration)}
          </p>
        </div>
        <Button asChild variant="ghost" size="sm">
          <a href={video.url} target="_blank" rel="noreferrer">
            <ExternalLink />
            Source
          </a>
        </Button>
      </div>
    </section>
  );
});
