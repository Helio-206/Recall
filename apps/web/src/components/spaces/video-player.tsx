"use client";

import { ExternalLink, Play } from "lucide-react";

import type { RecallVideo } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { formatDuration, getYouTubeEmbedUrl } from "@/lib/utils";

type VideoPlayerProps = {
  video?: RecallVideo | null;
};

export function VideoPlayer({ video }: VideoPlayerProps) {
  const embedUrl = video ? getYouTubeEmbedUrl(video.url) : null;

  if (!video) {
    return (
      <div className="grid aspect-video place-items-center rounded-lg border border-dashed border-border bg-surface/70 text-center shadow-insetPanel">
        <div>
          <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
            <Play className="size-5" />
          </div>
          <p className="mt-4 font-heading text-lg font-semibold text-foreground">No video selected</p>
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
          <p className="truncate font-heading text-base font-semibold text-foreground">{video.title}</p>
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
}
