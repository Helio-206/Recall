"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, ChevronRight, Circle, FileText, Loader2, Play } from "lucide-react";

import type { LearningModule } from "@recall/shared";
import { Progress } from "@/components/ui/progress";
import { cn, formatDuration } from "@/lib/utils";

type CurriculumSidebarProps = {
  modules: LearningModule[];
  activeVideoId: string | null;
  totalItems: number;
  completedItems: number;
  progress: number;
  isLoading?: boolean;
  error?: string | null;
  onSelectVideo: (videoId: string) => void;
};

export function CurriculumSidebar({
  modules,
  activeVideoId,
  totalItems,
  completedItems,
  progress,
  isLoading = false,
  error = null,
  onSelectVideo,
}: CurriculumSidebarProps) {
  const activeModuleId = useMemo(
    () =>
      modules.find((module) =>
        module.module_videos.some((entry) => entry.video_id === activeVideoId),
      )?.id ?? null,
    [activeVideoId, modules],
  );
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  useEffect(() => {
    const preferredId = activeModuleId ?? modules[0]?.id;
    if (!preferredId) return;
    setExpandedIds((current) =>
      current.includes(preferredId) ? current : [...current, preferredId],
    );
  }, [activeModuleId, modules]);

  return (
    <aside className="flex min-h-[440px] flex-col border-l border-border/70 bg-background xl:sticky xl:top-7 xl:h-[calc(100vh-3.5rem)]">
      <header className="border-b border-border/70 px-5 py-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="font-heading text-sm font-semibold text-foreground">Curriculum</h2>
            <p className="mt-1 text-xs text-muted">
              {completedItems} of {totalItems} lessons complete
            </p>
          </div>
          <span className="font-mono text-xs text-warm">{progress}%</span>
        </div>
        <Progress value={progress} className="mt-3 h-1 bg-white/[0.07] [&>div]:bg-warm" />
      </header>

      <div className="thin-scrollbar min-h-0 flex-1 overflow-y-auto pb-24">
        {isLoading && !modules.length ? (
          <div className="grid place-items-center py-16 text-muted">
            <Loader2 className="size-4 animate-spin" />
          </div>
        ) : error && !modules.length ? (
          <p className="px-5 py-8 text-sm leading-6 text-muted">{error}</p>
        ) : (
          modules.map((module) => {
            const isExpanded = expandedIds.includes(module.id);
            const isComplete =
              module.video_count > 0 && module.completed_count === module.video_count;

            return (
              <section key={module.id} className="border-b border-border/60">
                <button
                  type="button"
                  aria-expanded={isExpanded}
                  onClick={() =>
                    setExpandedIds((current) =>
                      current.includes(module.id)
                        ? current.filter((item) => item !== module.id)
                        : [...current, module.id],
                    )
                  }
                  className="flex w-full items-center gap-3 px-5 py-3 text-left transition-colors duration-200 hover:bg-white/[0.025]"
                >
                  <span
                    className={cn(
                      "grid size-5 shrink-0 place-items-center rounded-full border text-[10px]",
                      isComplete
                        ? "border-success/35 bg-success/10 text-success"
                        : "border-border text-muted",
                    )}
                  >
                    {isComplete ? <Check className="size-3" /> : module.order_index + 1}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-foreground">
                      {module.title}
                    </span>
                    <span className="mt-0.5 block text-[11px] text-muted">
                      {module.completed_count}/{module.video_count} lessons
                    </span>
                  </span>
                  {isExpanded ? (
                    <ChevronDown className="size-4 shrink-0 text-muted" />
                  ) : (
                    <ChevronRight className="size-4 shrink-0 text-muted" />
                  )}
                </button>

                <AnimatePresence initial={false}>
                  {isExpanded ? (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="pb-2">
                        {module.module_videos.map((entry) => {
                          const isActive = activeVideoId === entry.video_id;
                          return (
                            <button
                              key={entry.id}
                              type="button"
                              aria-current={isActive ? "step" : undefined}
                              onClick={() => onSelectVideo(entry.video_id)}
                              className={cn(
                                "relative flex w-full items-start gap-3 px-5 py-2.5 text-left transition-colors duration-200",
                                isActive
                                  ? "bg-primary/[0.09] text-foreground"
                                  : "text-muted hover:bg-white/[0.025] hover:text-foreground",
                              )}
                            >
                              {isActive ? (
                                <motion.span
                                  layoutId="curriculum-active"
                                  className="absolute inset-y-1 left-0 w-0.5 rounded-full bg-primary"
                                />
                              ) : null}
                              <span className="mt-0.5 grid size-4 shrink-0 place-items-center">
                                {entry.video.completed ? (
                                  <Check className="size-3.5 text-success" />
                                ) : isActive ? (
                                  <Play className="size-3.5 fill-primary text-primary" />
                                ) : (
                                  <Circle className="size-3 text-muted/70" />
                                )}
                              </span>
                              <span className="min-w-0 flex-1">
                                <span className="line-clamp-2 text-sm leading-5">
                                  {entry.order_index + 1}. {entry.video.title}
                                </span>
                                <span className="mt-1 flex items-center gap-2 text-[11px] text-muted">
                                  <span>{formatDuration(entry.video.duration)}</span>
                                  {entry.video.transcript_status === "completed" ? (
                                    <>
                                      <span aria-hidden="true">·</span>
                                      <span className="inline-flex items-center gap-1">
                                        <FileText className="size-3" />
                                        Transcript
                                      </span>
                                    </>
                                  ) : null}
                                </span>
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </section>
            );
          })
        )}
      </div>
    </aside>
  );
}
