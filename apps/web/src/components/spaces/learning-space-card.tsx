"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight, BookOpen, Clock3 } from "lucide-react";

import type { RecallSpace } from "@recall/shared";
import { LevelBadge } from "@/components/level-badge";
import { ProgressBar } from "@/components/progress-bar";
import { Badge } from "@/components/ui/badge";
import { formatShortDate } from "@/lib/utils";

type LearningSpaceCardProps = {
  space: RecallSpace;
};

export function LearningSpaceCard({ space }: LearningSpaceCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
    >
      <Link
        href={`/spaces/${space.id}`}
        className="group block h-full rounded-lg border border-border bg-surface/85 p-5 shadow-insetPanel transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/45 hover:bg-surface-2"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate font-heading text-base font-semibold text-foreground">
                {space.title}
              </h3>
              <LevelBadge progress={space.progress} />
            </div>
            <p className="mt-3 line-clamp-2 min-h-11 text-sm leading-6 text-muted">
              {space.description || "A structured path for focused video learning."}
            </p>
          </div>
          <span className="grid size-9 shrink-0 place-items-center rounded-md border border-border bg-background/80 text-muted transition-colors group-hover:border-primary/40 group-hover:text-foreground">
            <ArrowUpRight className="size-4" />
          </span>
        </div>

        <div className="mt-5">
          <ProgressBar value={space.progress} label="Progress" />
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2 text-xs text-muted">
          {space.topic && <Badge variant="neutral">{space.topic}</Badge>}
          <span className="inline-flex items-center gap-1.5">
            <BookOpen className="size-3.5" />
            {space.video_count} videos
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Clock3 className="size-3.5" />
            {formatShortDate(space.updated_at)}
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
