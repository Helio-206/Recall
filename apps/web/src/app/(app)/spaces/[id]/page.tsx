"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowRight, CheckCircle2, Layers3, PlayCircle, Plus, Target } from "lucide-react";

import type { RecallVideo } from "@recall/shared";
import { LearningIntelligencePanel } from "@/components/ai/learning-intelligence-panel";
import { LevelBadge } from "@/components/level-badge";
import { VideoNotesPanel } from "@/components/notes/video-notes-panel";
import { ProgressBar } from "@/components/progress-bar";
import { AddVideoDialog } from "@/components/spaces/add-video-dialog";
import { VideoCard } from "@/components/spaces/video-card";
import { VideoPlayer, type VideoPlayerHandle } from "@/components/spaces/video-player";
import { TranscriptPanel } from "@/components/transcript/transcript-panel";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAISummary } from "@/hooks/use-ai-summary";
import { formatDuration } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useSpaceStore } from "@/stores/space-store";

export default function SpaceDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const token = useAuthStore((state) => state.token);
  const { selectedSpace, fetchSpace, updateVideo, isLoading, error } = useSpaceStore();
  const [updatingVideoId, setUpdatingVideoId] = useState<string | null>(null);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [activeTimestamp, setActiveTimestamp] = useState<number | null>(null);
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0);
  const playerRef = useRef<VideoPlayerHandle | null>(null);

  useEffect(() => {
    if (token && params.id) void fetchSpace(token, params.id);
  }, [fetchSpace, params.id, token]);

  useEffect(() => {
    const videos = selectedSpace?.videos ?? [];
    if (!videos.length) {
      setActiveVideoId(null);
      return;
    }

    const requestedVideoId = searchParams.get("video");
    if (requestedVideoId && videos.some((video) => video.id === requestedVideoId)) {
      setActiveVideoId(requestedVideoId);
      return;
    }

    const activeVideoExists = videos.some((video) => video.id === activeVideoId);
    if (!activeVideoId || !activeVideoExists) {
      const nextVideo = videos.find((video) => !video.completed) ?? videos[0];
      setActiveVideoId(nextVideo.id);
    }
  }, [activeVideoId, searchParams, selectedSpace?.videos]);

  const onTranscriptCompleted = useCallback(async () => {
    if (!token || !params.id) return;
    await fetchSpace(token, params.id);
  }, [fetchSpace, params.id, token]);

  const videos = selectedSpace?.videos ?? [];
  const nextVideo = videos.find((video) => !video.completed) ?? videos[0];
  const activeVideo = videos.find((video) => video.id === activeVideoId) ?? nextVideo ?? null;
  const totalDuration = videos.reduce((sum, video) => sum + (video.duration || 0), 0);

  const aiSummary = useAISummary({
    token,
    videoId: activeVideo?.id ?? null,
  });

  const handleSeek = useCallback((seconds: number) => {
    setActiveTimestamp(seconds);
    playerRef.current?.seekTo(seconds);
  }, []);

  async function onToggle(video: RecallVideo) {
    if (!token) return;
    setUpdatingVideoId(video.id);
    try {
      await updateVideo(token, video.id, { completed: !video.completed });
    } finally {
      setUpdatingVideoId(null);
    }
  }

  useEffect(() => {
    setActiveTimestamp(null);
    setCurrentPlaybackTime(0);
  }, [activeVideo?.id]);

  useEffect(() => {
    const nextTab = searchParams.get("tab");
    if (nextTab === "transcript" || nextTab === "ai-summary" || nextTab === "notes") {
      setActiveTab(nextTab);
    }
  }, [searchParams]);

  useEffect(() => {
    const requestedVideoId = searchParams.get("video");
    const requestedTime = Number(searchParams.get("t") || 0);
    if (!requestedVideoId || !activeVideo || activeVideo.id !== requestedVideoId) return;
    if (!Number.isFinite(requestedTime) || requestedTime <= 0) return;
    setActiveTimestamp(requestedTime);
    playerRef.current?.seekTo(requestedTime);
  }, [activeVideo, searchParams]);

  if (isLoading && !selectedSpace) {
    return <div className="h-[70vh] animate-pulse rounded-lg border border-border bg-surface/70" />;
  }

  if (error || !selectedSpace) {
    return (
      <div className="rounded-lg border border-border bg-surface/80 p-8 text-muted">
        {error || "Learning space not found."}
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <header className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <LevelBadge progress={selectedSpace.progress} />
              {selectedSpace.topic && (
                <span className="rounded-md border border-border bg-background/70 px-2 py-0.5 text-xs text-muted">
                  {selectedSpace.topic}
                </span>
              )}
            </div>
            <h1 className="mt-3 font-heading text-3xl font-semibold text-foreground sm:text-4xl">
              {selectedSpace.title}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
              {selectedSpace.description || "A focused path for structured video learning."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <AddVideoDialog
              spaces={[selectedSpace]}
              spaceId={selectedSpace.id}
              trigger={
                <Button variant="secondary">
                  <Plus />
                  Add Video
                </Button>
              }
            />
            {nextVideo && (
              <Button type="button" onClick={() => setActiveVideoId(nextVideo.id)}>
                Continue
                <ArrowRight />
              </Button>
            )}
          </div>
        </div>
        <div className="mt-6">
          <ProgressBar value={selectedSpace.progress} label="Path completion" />
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
        <aside className="rounded-lg border border-border bg-surface/80 p-4 shadow-insetPanel xl:sticky xl:top-8 xl:h-[calc(100vh-4rem)] xl:overflow-auto">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-heading text-base font-semibold text-foreground">Curriculum</h2>
            <span className="font-mono text-xs text-muted">{videos.length} items</span>
          </div>
          <div className="mt-4 grid gap-2">
            {videos.map((video) => (
              <button
                key={video.id}
                type="button"
                onClick={() => setActiveVideoId(video.id)}
                className={[
                  "grid grid-cols-[auto_1fr] gap-3 rounded-md border p-3 text-left transition-all hover:border-primary/40 hover:bg-white/[0.05]",
                  activeVideo?.id === video.id
                    ? "border-primary/55 bg-primary/10"
                    : "border-border bg-background/55",
                ].join(" ")}
              >
                <span className="mt-0.5 text-muted">
                  {video.completed ? (
                    <CheckCircle2 className="size-4 text-success" />
                  ) : (
                    <PlayCircle className="size-4" />
                  )}
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-sm text-foreground">{video.title}</span>
                  <span className="mt-1 block text-xs text-muted">
                    {formatDuration(video.duration)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </aside>

        <section className="grid min-w-0 gap-5">
          <div className="min-w-0">
            <VideoPlayer
              ref={playerRef}
              video={activeVideo}
              onTimeUpdate={(seconds) => setCurrentPlaybackTime(seconds)}
            />

            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mt-5">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="transcript">Transcript</TabsTrigger>
                <TabsTrigger value="ai-summary">AI Summary</TabsTrigger>
                <TabsTrigger value="notes">Notes</TabsTrigger>
              </TabsList>

              <TabsContent value="overview">
                <div className="grid gap-4 md:grid-cols-3">
                  <Metric label="Progress" value={`${selectedSpace.progress}%`} icon={Target} />
                  <Metric
                    label="Completed"
                    value={selectedSpace.completed_count}
                    icon={CheckCircle2}
                  />
                  <Metric label="Duration" value={formatDuration(totalDuration)} icon={Layers3} />
                </div>

                <div className="mt-5 rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h2 className="font-heading text-lg font-semibold text-foreground">
                        Continue Learning
                      </h2>
                      <p className="mt-1 text-sm text-muted">
                        {nextVideo ? nextVideo.title : "Add a video to begin this path."}
                      </p>
                    </div>
                    {nextVideo ? (
                      <Button type="button" onClick={() => setActiveVideoId(nextVideo.id)}>
                        Open Video
                        <ArrowRight />
                      </Button>
                    ) : (
                      <AddVideoDialog
                        spaces={[selectedSpace]}
                        spaceId={selectedSpace.id}
                        trigger={<Button>Add Video</Button>}
                      />
                    )}
                  </div>
                </div>

                <div className="mt-5 grid gap-3">
                  {videos.length > 0 ? (
                    videos.map((video) => (
                      <VideoCard
                        key={video.id}
                        video={video}
                        onSelect={(selectedVideo) => setActiveVideoId(selectedVideo.id)}
                        onToggle={onToggle}
                        isActive={activeVideo?.id === video.id}
                        isUpdating={updatingVideoId === video.id}
                      />
                    ))
                  ) : (
                    <div className="rounded-lg border border-dashed border-border bg-surface/60 p-8 text-center">
                      <h2 className="font-heading text-lg font-semibold text-foreground">
                        No videos yet
                      </h2>
                      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
                        Paste a YouTube link to start building this learning path.
                      </p>
                      <AddVideoDialog
                        spaces={[selectedSpace]}
                        spaceId={selectedSpace.id}
                        trigger={<Button className="mt-5">Add Video</Button>}
                      />
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="transcript">
                <TranscriptPanel
                  video={activeVideo}
                  token={token}
                  onCompleted={onTranscriptCompleted}
                  activeTimestamp={activeTimestamp ?? currentPlaybackTime}
                  onSeek={handleSeek}
                />
              </TabsContent>

              <TabsContent value="ai-summary">
                <LearningIntelligencePanel
                  video={activeVideo}
                  insights={aiSummary.insights}
                  state={aiSummary.state}
                  error={aiSummary.error}
                  message={aiSummary.message}
                  isWorking={aiSummary.isWorking}
                  onGenerate={aiSummary.generate}
                  onSeek={handleSeek}
                />
              </TabsContent>

              <TabsContent value="notes">
                <VideoNotesPanel
                  video={activeVideo}
                  token={token}
                  currentTimestamp={currentPlaybackTime}
                  insights={aiSummary.insights}
                  onSeek={handleSeek}
                />
              </TabsContent>
            </Tabs>
          </div>
        </section>
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
