"use client";

import { useEffect } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock3,
  FolderPlus,
  Plus,
  Target,
} from "lucide-react";

import { AddVideoDialog } from "@/components/spaces/add-video-dialog";
import { CreateSpaceDialog } from "@/components/spaces/create-space-dialog";
import { LearningSpaceCard } from "@/components/spaces/learning-space-card";
import { Button } from "@/components/ui/button";
import { formatShortDate } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useSpaceStore } from "@/stores/space-store";

export default function DashboardPage() {
  const { token, user } = useAuthStore();
  const { spaces, fetchSpaces, isLoading, error } = useSpaceStore();

  useEffect(() => {
    if (token) void fetchSpaces(token);
  }, [fetchSpaces, token]);

  const totalVideos = spaces.reduce((sum, space) => sum + space.video_count, 0);
  const completedVideos = spaces.reduce((sum, space) => sum + space.completed_count, 0);
  const averageProgress = spaces.length
    ? Math.round(spaces.reduce((sum, space) => sum + space.progress, 0) / spaces.length)
    : 0;
  const activity =
    spaces.length > 0
      ? spaces.slice(0, 3).map((space) => ({
          id: space.id,
          label: space.title,
          detail: `${space.completed_count}/${space.video_count} videos complete`,
          created_at: space.updated_at,
        }))
      : [];

  const primarySpace = spaces[0] || null;

  return (
    <div className="grid gap-6">
      <header className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
            <p className="text-sm text-muted">Welcome back, {user?.name?.split(" ")[0] || "friend"}.</p>
            <h1 className="mt-2 font-heading text-3xl font-semibold text-foreground sm:text-4xl">
              Learning Dashboard
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
              Organize your spaces, track progress, and continue where you left off.
            </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <CreateSpaceDialog
            trigger={
              <Button variant="secondary">
                <FolderPlus />
                New Space
              </Button>
            }
          />
          {spaces.length > 0 ? (
            <AddVideoDialog
              spaces={spaces}
              trigger={
                <Button>
                  <Plus />
                  Add Source
                </Button>
              }
            />
          ) : null}
        </div>
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Spaces" value={spaces.length} icon={BookOpen} />
        <Stat label="Videos" value={totalVideos} icon={Clock3} />
        <Stat label="Completed" value={completedVideos} icon={CheckCircle2} />
        <Stat label="Focus" value={`${averageProgress}%`} icon={Target} />
      </section>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <section className="min-w-0">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="font-heading text-lg font-semibold text-foreground">Learning Spaces</h2>
              <p className="mt-1 text-sm text-muted">{spaces.length || "No"} active paths</p>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/spaces">
                View all
                <ArrowRight />
              </Link>
            </Button>
          </div>

          {isLoading ? (
            <div className="grid gap-3 md:grid-cols-2">
              {[1, 2].map((item) => (
                <div key={item} className="h-56 animate-pulse rounded-lg border border-border bg-surface/70" />
              ))}
            </div>
          ) : spaces.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {spaces.slice(0, 4).map((space) => (
                <LearningSpaceCard key={space.id} space={space} />
              ))}
            </div>
          ) : (
            <EmptyState />
          )}
        </section>

        <aside className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <h2 className="font-heading text-lg font-semibold text-foreground">Snapshot</h2>
          {primarySpace ? (
            <div className="mt-4 rounded-md border border-border bg-background/55 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-muted">Current focus</p>
              <p className="mt-2 line-clamp-2 text-sm font-medium text-foreground">{primarySpace.title}</p>
              <p className="mt-2 text-xs text-muted">
                {primarySpace.completed_count}/{primarySpace.video_count} completed • {primarySpace.progress}%
              </p>
            </div>
          ) : null}

          <h3 className="mt-5 text-sm font-semibold text-foreground">Recent Activity</h3>
          {error ? (
            <div className="mt-5 rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100">
              Unable to load your spaces right now. {error}
            </div>
          ) : activity.length > 0 ? (
            <div className="mt-5 grid gap-3">
              {activity.map((item) => (
                <div key={item.id} className="rounded-md border border-border bg-background/55 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">{item.label}</p>
                      <p className="mt-1 text-xs leading-5 text-muted">{item.detail}</p>
                    </div>
                    <span className="shrink-0 font-mono text-xs text-muted">
                      {formatShortDate(item.created_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-5 rounded-md border border-dashed border-border bg-background/40 p-4 text-sm text-muted">
              No recent activity yet.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function Stat({
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

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface/60 p-8 text-center">
      <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
        <FolderPlus className="size-5" />
      </div>
      <h3 className="mt-4 font-heading text-lg font-semibold text-foreground">Create your first space</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
        Start with a topic, then add videos into an ordered curriculum.
      </p>
      <CreateSpaceDialog trigger={<Button className="mt-5">New Space</Button>} />
    </div>
  );
}

