"use client";

import { useEffect, useMemo, useRef } from "react";
import { motion } from "framer-motion";
import { Check, ChevronLeft, ChevronRight, Play } from "lucide-react";

import type { LearningModule } from "@recall/shared";
import { Button } from "@/components/ui/button";
import { cn, formatDuration } from "@/lib/utils";

type LessonRailProps = {
  modules: LearningModule[];
  activeVideoId: string | null;
  onSelectVideo: (videoId: string) => void;
};

export function LessonRail({ modules, activeVideoId, onSelectVideo }: LessonRailProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const activeRef = useRef<HTMLButtonElement | null>(null);
  const lessons = useMemo(
    () =>
      modules.flatMap((module) =>
        module.module_videos.map((entry) => ({
          ...entry,
          moduleOrder: module.order_index,
        })),
      ),
    [modules],
  );
  const activeIndex = lessons.findIndex((lesson) => lesson.video_id === activeVideoId);

  useEffect(() => {
    activeRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }, [activeVideoId]);

  function selectOffset(offset: -1 | 1) {
    if (activeIndex < 0) return;
    const target = lessons[activeIndex + offset];
    if (target) onSelectVideo(target.video_id);
  }

  if (!lessons.length) return null;

  return (
    <nav
      aria-label="Lesson navigation"
      className="sticky bottom-20 z-20 mt-5 flex h-[92px] items-stretch border border-border/80 bg-surface/95 shadow-premium backdrop-blur-xl lg:bottom-4"
    >
      <Button
        type="button"
        size="icon"
        variant="ghost"
        className="h-full w-11 shrink-0 rounded-none border-r border-border/70"
        disabled={activeIndex <= 0}
        onClick={() => selectOffset(-1)}
        aria-label="Previous lesson"
      >
        <ChevronLeft />
      </Button>

      <div ref={scrollRef} className="thin-scrollbar flex min-w-0 flex-1 snap-x overflow-x-auto">
        {lessons.map((lesson) => {
          const isActive = lesson.video_id === activeVideoId;
          return (
            <button
              key={lesson.id}
              ref={isActive ? activeRef : undefined}
              type="button"
              aria-current={isActive ? "page" : undefined}
              onClick={() => onSelectVideo(lesson.video_id)}
              className={cn(
                "relative flex w-48 shrink-0 snap-start flex-col justify-center border-r border-border/60 px-4 text-left transition-colors duration-200 hover:bg-white/[0.035]",
                isActive && "bg-primary/[0.08]",
              )}
            >
              {isActive ? (
                <motion.span
                  layoutId="lesson-rail-active"
                  className="absolute inset-x-0 top-0 h-0.5 bg-primary"
                />
              ) : null}
              <span className="flex items-center gap-2 font-mono text-[11px] text-muted">
                <span>
                  {lesson.moduleOrder + 1}.{lesson.order_index + 1}
                </span>
                {lesson.video.completed ? (
                  <Check className="size-3 text-success" />
                ) : isActive ? (
                  <Play className="size-3 fill-primary text-primary" />
                ) : null}
              </span>
              <span
                className={cn(
                  "mt-1 line-clamp-2 text-xs font-medium leading-4",
                  isActive ? "text-primary" : "text-foreground",
                )}
              >
                {lesson.video.title}
              </span>
              <span className="mt-1 text-[11px] text-muted">
                {formatDuration(lesson.video.duration)}
              </span>
            </button>
          );
        })}
      </div>

      <Button
        type="button"
        size="icon"
        variant="ghost"
        className="h-full w-11 shrink-0 rounded-none border-l border-border/70"
        disabled={activeIndex < 0 || activeIndex >= lessons.length - 1}
        onClick={() => selectOffset(1)}
        aria-label="Next lesson"
      >
        <ChevronRight />
      </Button>
    </nav>
  );
}
