"use client";

import { AlertCircle, ArrowRight, CheckCircle2, Layers3, Loader2, Sparkles, Target } from "lucide-react";

import type { CurriculumHealth, LearningModule, RecallSpace, RecallVideo, SuggestedNextVideo } from "@recall/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { VideoCard } from "@/components/spaces/video-card";
import { ProgressBar } from "@/components/progress-bar";
import { formatDuration } from "@/lib/utils";

type CurriculumOverviewProps = {
  space: RecallSpace;
  modules: LearningModule[];
  health: CurriculumHealth | null;
  nextVideo: RecallVideo | null;
  suggestedNextVideo: SuggestedNextVideo | null;
  activeVideoId: string | null;
  updatingVideoId: string | null;
  isRebuilding: boolean;
  onSelectVideo: (video: RecallVideo) => void;
  onToggleVideo: (video: RecallVideo) => void;
  onRebuild: () => void;
};

export function CurriculumOverview({
  space,
  modules,
  health,
  nextVideo,
  suggestedNextVideo,
  activeVideoId,
  updatingVideoId,
  isRebuilding,
  onSelectVideo,
  onToggleVideo,
  onRebuild,
}: CurriculumOverviewProps) {
  const totalDuration = (space.videos ?? []).reduce((sum, video) => sum + (video.duration || 0), 0);

  return (
    <div className="grid gap-5">
      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Progress" value={`${space.progress}%`} icon={Target} />
        <Metric label="Completed" value={space.completed_count} icon={CheckCircle2} />
        <Metric label="Duration" value={formatDuration(totalDuration)} icon={Layers3} />
        <Metric label="Health" value={health ? `${health.score}/100` : "Pending"} icon={Sparkles} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="default">Suggested Next Lesson</Badge>
                {suggestedNextVideo && <Badge variant="neutral">{suggestedNextVideo.module_title}</Badge>}
              </div>
              <h2 className="mt-3 font-heading text-lg font-semibold text-foreground">
                {nextVideo ? nextVideo.title : "Rebuild the curriculum to generate a next step."}
              </h2>
              <p className="mt-2 text-sm leading-6 text-muted">
                {suggestedNextVideo?.reason || "Use curriculum reconstruction to unlock the recommended next lesson."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="secondary" onClick={onRebuild} disabled={isRebuilding}>
                {isRebuilding ? <Loader2 className="animate-spin" /> : <Sparkles />}
                Rebuild Curriculum
              </Button>
              {nextVideo && (
                <Button type="button" onClick={() => onSelectVideo(nextVideo)}>
                  Open Lesson
                  <ArrowRight />
                </Button>
              )}
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-heading text-lg font-semibold text-foreground">Curriculum Health</h2>
            {health && <Badge variant={health.score >= 80 ? "success" : health.score >= 60 ? "warm" : "neutral"}>{health.score}</Badge>}
          </div>
          {health ? (
            <div className="mt-4 space-y-4">
              <ProgressBar value={health.score} label="Readiness" />
              <div className="grid gap-2 text-sm text-muted sm:grid-cols-2">
                <HealthRow label="Dependencies" value={health.dependency_count} />
                <HealthRow label="Manual Overrides" value={health.manual_override_count} />
                <HealthRow label="Missing Transcripts" value={health.missing_transcript_count} />
                <HealthRow label="Duplicate Topics" value={health.duplicate_topic_count} />
              </div>
              {health.warnings.length > 0 ? (
                <div className="space-y-2">
                  {health.warnings.map((warning) => (
                    <div
                      key={warning}
                      className="flex items-start gap-2 rounded-md border border-border bg-background/60 px-3 py-2 text-xs text-muted"
                    >
                      <AlertCircle className="mt-0.5 size-4 text-warm" />
                      <span>{warning}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted">No curriculum risks detected in the latest reconstruction.</p>
              )}
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted">Health metrics appear after the first reconstruction run.</p>
          )}
        </section>
      </div>

      <div className="grid gap-4">
        {modules.map((module) => (
          <section key={module.id} className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
            <div className="flex flex-col gap-3 border-b border-border pb-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="neutral">Module {module.order_index + 1}</Badge>
                  <Badge variant={module.difficulty_level === "Advanced" ? "warm" : module.difficulty_level === "Beginner" ? "success" : "neutral"}>
                    {module.difficulty_level}
                  </Badge>
                </div>
                <h2 className="mt-3 font-heading text-xl font-semibold text-foreground">{module.title}</h2>
                {module.description && <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{module.description}</p>}
              </div>
              <div className="min-w-[180px]">
                <ProgressBar value={module.progress} label={`${module.completed_count}/${module.video_count} complete`} />
              </div>
            </div>

            {module.learning_objectives.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {module.learning_objectives.map((objective) => (
                  <Badge key={objective} variant="neutral">
                    {objective}
                  </Badge>
                ))}
              </div>
            )}

            <div className="mt-5 grid gap-3">
              {module.module_videos.map((entry) => (
                <VideoCard
                  key={entry.id}
                  video={entry.video}
                  onSelect={onSelectVideo}
                  onToggle={onToggleVideo}
                  isActive={activeVideoId === entry.video_id}
                  isUpdating={updatingVideoId === entry.video_id}
                  sequenceLabel={`${module.order_index + 1}.${entry.order_index + 1}`}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface/80 p-4 shadow-insetPanel">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-muted">{label}</span>
        <span className="grid size-8 place-items-center rounded-md border border-border bg-background/70 text-primary">
          <Icon className="size-4" />
        </span>
      </div>
      <div className="mt-4 font-heading text-2xl font-semibold text-foreground">{value}</div>
    </div>
  );
}

function HealthRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-background/50 px-3 py-2">
      <div className="text-[11px] uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 text-base text-foreground">{value}</div>
    </div>
  );
}