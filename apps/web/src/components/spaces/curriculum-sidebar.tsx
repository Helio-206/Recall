"use client";

import { useEffect, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
  Lock,
  PlayCircle,
  RefreshCw,
  RotateCcw,
} from "lucide-react";

import type { LearningModule } from "@recall/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, formatDuration } from "@/lib/utils";

type CurriculumSidebarProps = {
  modules: LearningModule[];
  activeVideoId: string | null;
  totalItems: number;
  healthScore: number | null;
  jobStatus: string | null;
  isLoading?: boolean;
  error?: string | null;
  isRebuilding?: boolean;
  overrideVideoId?: string | null;
  onSelectVideo: (videoId: string) => void;
  onRebuild: () => void;
  onMoveVideo: (videoId: string, direction: -1 | 1) => void;
  onSetVideoOrder: (videoId: string, moduleTitle: string, orderIndex: number) => void;
  onResetVideo: (videoId: string) => void;
};

export function CurriculumSidebar({
  modules,
  activeVideoId,
  totalItems,
  healthScore,
  jobStatus,
  isLoading = false,
  error = null,
  isRebuilding = false,
  overrideVideoId = null,
  onSelectVideo,
  onRebuild,
  onMoveVideo,
  onSetVideoOrder,
  onResetVideo,
}: CurriculumSidebarProps) {
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  useEffect(() => {
    setExpandedIds((current) => {
      const next = new Set(current);
      for (const learningModule of modules) next.add(learningModule.id);
      return Array.from(next);
    });
  }, [modules]);

  return (
    <div className="overflow-x-hidden rounded-lg border border-border bg-surface/80 p-4 shadow-insetPanel xl:sticky xl:top-8 xl:h-[calc(100vh-4rem)] xl:overflow-y-auto">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-heading text-base font-semibold text-foreground">Curriculum</h2>
            {healthScore !== null && (
              <Badge variant={healthScore >= 80 ? "success" : healthScore >= 60 ? "warm" : "neutral"}>
                {healthScore}
              </Badge>
            )}
          </div>
          <p className="mt-1 text-xs text-muted">
            {totalItems} lessons across {modules.length} modules
          </p>
          <p className="mt-1 text-xs text-muted">Ajustes de ordem sao salvos automaticamente.</p>
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={onRebuild} disabled={isRebuilding}>
          {isRebuilding ? <Loader2 className="animate-spin" /> : <RefreshCw />}
          Rebuild
        </Button>
      </div>

      {jobStatus && (
        <div className="mt-3 rounded-md border border-border bg-background/60 px-3 py-2 text-xs text-muted">
          Reconstruction status: <span className="text-foreground">{jobStatus}</span>
        </div>
      )}

      {error && !modules.length && (
        <div className="mt-4 rounded-md border border-border bg-background/60 p-3 text-sm text-muted">
          {error}
        </div>
      )}

      <div className="mt-4 grid gap-3">
        {isLoading && !modules.length ? (
          <div className="space-y-2">
            <div className="h-20 animate-pulse rounded-lg border border-border bg-background/60" />
            <div className="h-20 animate-pulse rounded-lg border border-border bg-background/60" />
          </div>
        ) : (
          modules.map((module) => {
            const isExpanded = expandedIds.includes(module.id);
            return (
              <section key={module.id} className="rounded-lg border border-border bg-background/55">
                <button
                  type="button"
                  onClick={() =>
                    setExpandedIds((current) =>
                      current.includes(module.id)
                        ? current.filter((item) => item !== module.id)
                        : [...current, module.id],
                    )
                  }
                  className="flex w-full items-start justify-between gap-3 p-3 text-left"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted">
                        Module {module.order_index + 1}
                      </span>
                      <Badge variant={difficultyVariant(module.difficulty_level)}>
                        {module.difficulty_level}
                      </Badge>
                    </div>
                    <h3 className="mt-2 break-words text-sm font-medium text-foreground">{module.title}</h3>
                    {module.description && (
                      <p className="mt-1 break-words text-xs leading-5 text-muted">{module.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted">
                      <span>{module.progress}% complete</span>
                      <span>{module.video_count} lessons</span>
                      <span>{formatDuration((module.estimated_duration_minutes ?? 0) * 60)}</span>
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="mt-1 size-4 text-muted" />
                  ) : (
                    <ChevronRight className="mt-1 size-4 text-muted" />
                  )}
                </button>

                {isExpanded && (
                  <div className="border-t border-border px-2 pb-2 pt-1">
                    {module.module_videos.map((entry, index) => {
                      const isActive = activeVideoId === entry.video_id;
                      const isBusy = overrideVideoId === entry.video_id;
                      return (
                        <div
                          key={entry.id}
                          className={cn(
                            "mt-2 overflow-x-hidden rounded-md border p-2 transition-colors",
                            isActive
                              ? "border-primary/45 bg-primary/10"
                              : "border-border bg-surface/50",
                          )}
                        >
                          <div className="flex items-start gap-2">
                            <button
                              type="button"
                              onClick={() => onSelectVideo(entry.video_id)}
                              className="flex min-w-0 flex-1 items-start gap-2 text-left"
                            >
                              <span className="mt-0.5 text-muted">
                                {entry.video.completed ? (
                                  <CheckCircle2 className="size-4 text-success" />
                                ) : (
                                  <PlayCircle className="size-4" />
                                )}
                              </span>
                                <span className="min-w-0">
                                  <span className="block break-words text-sm text-foreground">
                                  {module.order_index + 1}.{entry.order_index + 1} {entry.video.title}
                                </span>
                                <span className="mt-1 block text-[11px] text-muted">
                                  {entry.video.author || "Imported source"}
                                </span>
                              </span>
                            </button>

                            <div className="flex items-center gap-1">
                              <label className="sr-only" htmlFor={`order-${entry.id}`}>
                                Set lesson order
                              </label>
                              <select
                                id={`order-${entry.id}`}
                                value={entry.order_index}
                                disabled={isBusy}
                                onChange={(event) =>
                                  onSetVideoOrder(
                                    entry.video_id,
                                    module.title,
                                    Number(event.target.value),
                                  )
                                }
                                className="h-7 rounded border border-border bg-background px-2 text-xs text-foreground"
                              >
                                {module.module_videos.map((_, positionIndex) => (
                                  <option key={`${entry.id}-${positionIndex}`} value={positionIndex}>
                                    {positionIndex + 1}
                                  </option>
                                ))}
                              </select>
                              <Button
                                type="button"
                                size="icon"
                                variant="ghost"
                                className="size-7"
                                disabled={isBusy || index === 0}
                                onClick={() => onMoveVideo(entry.video_id, -1)}
                                aria-label={`Move ${entry.video.title} earlier`}
                              >
                                <ArrowUp className="size-3.5" />
                              </Button>
                              <Button
                                type="button"
                                size="icon"
                                variant="ghost"
                                className="size-7"
                                disabled={isBusy || index === module.module_videos.length - 1}
                                onClick={() => onMoveVideo(entry.video_id, 1)}
                                aria-label={`Move ${entry.video.title} later`}
                              >
                                <ArrowDown className="size-3.5" />
                              </Button>
                              <Button
                                type="button"
                                size="icon"
                                variant="ghost"
                                className="size-7"
                                disabled={isBusy}
                                onClick={() => onResetVideo(entry.video_id)}
                                aria-label={`Reset manual order for ${entry.video.title}`}
                              >
                                {entry.is_manual_override ? (
                                  <Lock className="size-3.5 text-primary" />
                                ) : isBusy ? (
                                  <Loader2 className="size-3.5 animate-spin" />
                                ) : (
                                  <RotateCcw className="size-3.5" />
                                )}
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })
        )}
      </div>
    </div>
  );
}

function difficultyVariant(level: LearningModule["difficulty_level"]) {
  if (level === "Advanced") return "warm";
  if (level === "Beginner") return "success";
  return "neutral";
}