"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowRight, Loader2, Plus, Sparkles } from "lucide-react";

import type { LearningModule, RecallVideo, SpaceCurriculum } from "@recall/shared";
import { LearningIntelligencePanel } from "@/components/ai/learning-intelligence-panel";
import { VideoNotesPanel } from "@/components/notes/video-notes-panel";
import { AddVideoDialog } from "@/components/spaces/add-video-dialog";
import { CurriculumOverview } from "@/components/spaces/curriculum-overview";
import { CurriculumSidebar } from "@/components/spaces/curriculum-sidebar";
import { VideoPlayer, type VideoPlayerHandle } from "@/components/spaces/video-player";
import { TranscriptPanel } from "@/components/transcript/transcript-panel";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAISummary } from "@/hooks/use-ai-summary";
import { useAuthStore } from "@/stores/auth-store";
import { useSpaceStore } from "@/stores/space-store";

export default function SpaceDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const token = useAuthStore((state) => state.token);
  const {
    selectedSpace,
    selectedCurriculum,
    fetchSpace,
    fetchCurriculum,
    updateVideo,
    rebuildCurriculum,
    updateCurriculumOverride,
    isLoading,
    isCurriculumLoading,
    error,
    curriculumError,
  } = useSpaceStore();
  const [updatingVideoId, setUpdatingVideoId] = useState<string | null>(null);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [activeTimestamp, setActiveTimestamp] = useState<number | null>(null);
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0);
  const [isRebuildingCurriculum, setIsRebuildingCurriculum] = useState(false);
  const [overrideVideoId, setOverrideVideoId] = useState<string | null>(null);
  const playerRef = useRef<VideoPlayerHandle | null>(null);

  useEffect(() => {
    if (token && params.id) void fetchSpace(token, params.id);
  }, [fetchSpace, params.id, token]);

  useEffect(() => {
    if (token && params.id) void fetchCurriculum(token, params.id);
  }, [fetchCurriculum, params.id, selectedSpace?.completed_count, selectedSpace?.video_count, token]);

  useEffect(() => {
    const status = selectedCurriculum?.latest_job?.status;
    if (!token || !params.id || (status !== "pending" && status !== "processing")) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void fetchCurriculum(token, params.id);
    }, 4000);

    return () => window.clearInterval(intervalId);
  }, [fetchCurriculum, params.id, selectedCurriculum?.latest_job?.status, token]);

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
  const modules = selectedCurriculum?.modules ?? buildFallbackModules(videos);
  const nextVideo =
    videos.find((video) => video.id === selectedCurriculum?.suggested_next_video?.video_id) ??
    videos.find((video) => !video.completed) ??
    videos[0];
  const activeVideo = videos.find((video) => video.id === activeVideoId) ?? nextVideo ?? null;

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

  async function onRebuildCurriculum() {
    if (!token || !params.id) return;
    setIsRebuildingCurriculum(true);
    try {
      await rebuildCurriculum(token, params.id, { force: true });
      await fetchCurriculum(token, params.id);
    } finally {
      setIsRebuildingCurriculum(false);
    }
  }

  async function onMoveVideo(videoId: string, direction: -1 | 1) {
    if (!token || !params.id || !selectedCurriculum) return;
    const entry = findCurriculumEntry(selectedCurriculum, videoId);
    if (!entry) return;

    const targetIndex = Math.max(0, entry.entry.order_index + direction);
    setOverrideVideoId(videoId);
    try {
      await updateCurriculumOverride(token, params.id, videoId, {
        module_title: entry.module.title,
        order_index: targetIndex,
        locked: true,
      });
    } finally {
      setOverrideVideoId(null);
    }
  }

  async function onResetVideo(videoId: string) {
    if (!token || !params.id || !selectedCurriculum) return;
    setOverrideVideoId(videoId);
    try {
      await updateCurriculumOverride(token, params.id, videoId, { locked: false });
    } finally {
      setOverrideVideoId(null);
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
              <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-0.5 text-xs text-blue-100">
                {selectedSpace.progress}% complete
              </span>
              {selectedSpace.topic && (
                <span className="rounded-md border border-border bg-background/70 px-2 py-0.5 text-xs text-muted">
                  {selectedSpace.topic}
                </span>
              )}
              {selectedCurriculum?.latest_job?.status && (
                <span className="rounded-md border border-border bg-background/70 px-2 py-0.5 text-xs text-muted">
                  Curriculum {selectedCurriculum.latest_job.status}
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
            <Button
              type="button"
              variant="secondary"
              onClick={onRebuildCurriculum}
              disabled={isRebuildingCurriculum}
            >
              {isRebuildingCurriculum ? <Loader2 className="animate-spin" /> : <Sparkles />}
              Rebuild Curriculum
            </Button>
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
      </header>

      <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
        <CurriculumSidebar
          modules={modules}
          activeVideoId={activeVideo?.id ?? null}
          totalItems={videos.length}
          healthScore={selectedCurriculum?.health.score ?? null}
          jobStatus={selectedCurriculum?.latest_job?.status ?? null}
          isLoading={isCurriculumLoading}
          error={curriculumError}
          isRebuilding={isRebuildingCurriculum}
          overrideVideoId={overrideVideoId}
          onSelectVideo={setActiveVideoId}
          onRebuild={onRebuildCurriculum}
          onMoveVideo={onMoveVideo}
          onResetVideo={onResetVideo}
        />

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
                <CurriculumOverview
                  space={selectedSpace}
                  modules={modules}
                  health={selectedCurriculum?.health ?? null}
                  nextVideo={nextVideo ?? null}
                  suggestedNextVideo={selectedCurriculum?.suggested_next_video ?? null}
                  activeVideoId={activeVideo?.id ?? null}
                  updatingVideoId={updatingVideoId}
                  isRebuilding={isRebuildingCurriculum}
                  onSelectVideo={(video) => setActiveVideoId(video.id)}
                  onToggleVideo={onToggle}
                  onRebuild={onRebuildCurriculum}
                />
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

function findCurriculumEntry(curriculum: SpaceCurriculum, videoId: string) {
  for (const learningModule of curriculum.modules) {
    const entry = learningModule.module_videos.find((item) => item.video_id === videoId);
    if (entry) {
      return { module: learningModule, entry };
    }
  }
  return null;
}

function buildFallbackModules(videos: RecallVideo[]): LearningModule[] {
  if (!videos.length) return [];
  const completedCount = videos.filter((video) => video.completed).length;
  const progress = Math.round((completedCount / videos.length) * 100);
  return [
    {
      id: "fallback-module",
      title: "Imported Sequence",
      description: "Current ingest order before curriculum reconstruction finishes.",
      order_index: 0,
      difficulty_level: "Intermediate",
      learning_objectives: [],
      estimated_duration_minutes: Math.round(
        videos.reduce((sum, video) => sum + (video.duration || 0), 0) / 60,
      ),
      rationale: "Fallback grouping derived from the existing lesson order.",
      confidence_score: 0,
      video_count: videos.length,
      completed_count: completedCount,
      progress,
      module_videos: videos.map((video, index) => ({
        id: `fallback-${video.id}`,
        video_id: video.id,
        order_index: index,
        rationale: null,
        confidence_score: 0,
        is_manual_override: false,
        video,
      })),
    },
  ];
}
