"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, CheckCircle2, Plus } from "lucide-react";

import type { LearningModule, RecallVideo } from "@recall/shared";
import { VideoNotesPanel } from "@/components/notes/video-notes-panel";
import { AddVideoDialog } from "@/components/spaces/add-video-dialog";
import { CurriculumSidebar } from "@/components/spaces/curriculum-sidebar";
import { LessonRail } from "@/components/spaces/lesson-rail";
import { VideoPlayer, type VideoPlayerHandle } from "@/components/spaces/video-player";
import { TranscriptPanel } from "@/components/transcript/transcript-panel";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
    isLoading,
    isCurriculumLoading,
    error,
    curriculumError,
  } = useSpaceStore();
  const [updatingVideoId, setUpdatingVideoId] = useState<string | null>(null);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("transcript");
  const [activeTimestamp, setActiveTimestamp] = useState<number | null>(null);
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0);
  const playerRef = useRef<VideoPlayerHandle | null>(null);
  const playerSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (token && params.id) void fetchSpace(token, params.id);
  }, [fetchSpace, params.id, token]);

  useEffect(() => {
    if (token && params.id) void fetchCurriculum(token, params.id);
  }, [
    fetchCurriculum,
    params.id,
    selectedSpace?.completed_count,
    selectedSpace?.video_count,
    token,
  ]);

  useEffect(() => {
    const status = selectedCurriculum?.latest_job?.status;
    if (!token || !params.id || (status !== "pending" && status !== "processing")) return;

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

    if (!activeVideoId || !videos.some((video) => video.id === activeVideoId)) {
      setActiveVideoId((videos.find((video) => !video.completed) ?? videos[0]).id);
    }
  }, [activeVideoId, searchParams, selectedSpace?.videos]);

  useEffect(() => {
    const nextTab = searchParams.get("tab");
    if (nextTab === "notes" || nextTab === "transcript") setActiveTab(nextTab);
    if (nextTab === "ai-summary") setActiveTab("transcript");
  }, [searchParams]);

  const videos = selectedSpace?.videos ?? [];
  const modules = selectedCurriculum?.modules ?? buildFallbackModules(videos);
  const orderedVideos = useMemo(
    () => modules.flatMap((module) => module.module_videos.map((entry) => entry.video)),
    [modules],
  );
  const suggestedVideo =
    videos.find((video) => video.id === selectedCurriculum?.suggested_next_video?.video_id) ??
    videos.find((video) => !video.completed) ??
    videos[0] ??
    null;
  const activeVideo = videos.find((video) => video.id === activeVideoId) ?? suggestedVideo ?? null;
  const activeIndex = orderedVideos.findIndex((video) => video.id === activeVideo?.id);
  const followingVideo =
    (activeVideo?.completed ? orderedVideos[activeIndex + 1] : activeVideo) ??
    suggestedVideo ??
    activeVideo;

  const onTranscriptCompleted = useCallback(async () => {
    if (!token || !params.id) return;
    await fetchSpace(token, params.id);
  }, [fetchSpace, params.id, token]);

  const handleSeek = useCallback((seconds: number) => {
    setActiveTimestamp(seconds);
    playerRef.current?.seekTo(seconds);
  }, []);

  const handleSelectVideo = useCallback((videoId: string) => {
    setActiveVideoId(videoId);
    setActiveTimestamp(null);
    setCurrentPlaybackTime(0);
  }, []);

  const handleContinue = useCallback(() => {
    if (followingVideo) handleSelectVideo(followingVideo.id);
    playerSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [followingVideo, handleSelectVideo]);

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
    const requestedVideoId = searchParams.get("video");
    const requestedTime = Number(searchParams.get("t") || 0);
    if (!requestedVideoId || !activeVideo || activeVideo.id !== requestedVideoId) return;
    if (!Number.isFinite(requestedTime) || requestedTime <= 0) return;
    setActiveTimestamp(requestedTime);
    playerRef.current?.seekTo(requestedTime);
  }, [activeVideo, searchParams]);

  if (isLoading && !selectedSpace) {
    return <div className="h-[70vh] animate-pulse border border-border bg-surface/70" />;
  }

  if (error || !selectedSpace) {
    return (
      <div className="border border-border bg-surface/80 p-8 text-muted">
        {error || "Learning space not found."}
      </div>
    );
  }

  return (
    <div className="pb-24">
      <header className="mb-4 flex flex-col gap-4 border-b border-border/70 pb-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <Link
            href="/spaces"
            className="inline-flex items-center gap-2 text-xs text-muted transition-colors hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" />
            Learning Spaces
          </Link>
          <div className="mt-3 flex flex-wrap items-end gap-x-4 gap-y-2">
            <h1 className="font-heading text-2xl font-semibold text-foreground">
              {selectedSpace.title}
            </h1>
            {selectedSpace.topic ? (
              <span className="pb-1 text-sm text-muted">{selectedSpace.topic}</span>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="w-44">
            <div className="mb-2 flex items-center justify-between gap-3 text-xs">
              <span className="text-muted">
                {selectedSpace.completed_count}/{selectedSpace.video_count} lessons
              </span>
              <span className="font-mono text-warm">{selectedSpace.progress}%</span>
            </div>
            <Progress
              value={selectedSpace.progress}
              className="h-1 bg-white/[0.07] [&>div]:bg-warm"
            />
          </div>
          <AddVideoDialog
            spaces={[selectedSpace]}
            spaceId={selectedSpace.id}
            trigger={
              <Button variant="secondary" size="sm">
                <Plus />
                Add Video
              </Button>
            }
          />
        </div>
      </header>

      <div className="grid min-w-0 xl:grid-cols-[minmax(0,1fr)_320px] 2xl:grid-cols-[minmax(0,1fr)_360px]">
        <main className="min-w-0 xl:pr-5">
          <div ref={playerSectionRef} className="scroll-mt-6">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={activeVideo?.id ?? "empty"}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
              >
                <VideoPlayer
                  ref={playerRef}
                  video={activeVideo}
                  onTimeUpdate={setCurrentPlaybackTime}
                />
              </motion.div>
            </AnimatePresence>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4 min-w-0">
            <div className="flex items-center justify-between gap-3 border-b border-border/70">
              <TabsList className="h-auto rounded-none border-0 bg-transparent p-0">
                <TabsTrigger
                  value="transcript"
                  className="rounded-none border-b-2 border-transparent px-3 py-2 data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:shadow-none"
                >
                  Transcript
                </TabsTrigger>
                <TabsTrigger
                  value="notes"
                  className="rounded-none border-b-2 border-transparent px-3 py-2 data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:shadow-none"
                >
                  Notes
                </TabsTrigger>
              </TabsList>

              {activeVideo ? (
                <Button
                  type="button"
                  size="sm"
                  variant={activeVideo.completed ? "secondary" : "ghost"}
                  disabled={updatingVideoId === activeVideo.id}
                  onClick={() => void onToggle(activeVideo)}
                >
                  <CheckCircle2 />
                  {activeVideo.completed ? "Completed" : "Mark complete"}
                </Button>
              ) : null}
            </div>

            <TabsContent value="transcript" className="mt-0">
              <TranscriptPanel
                video={activeVideo}
                token={token}
                onCompleted={onTranscriptCompleted}
                activeTimestamp={activeTimestamp ?? currentPlaybackTime}
                onSeek={handleSeek}
              />
            </TabsContent>

            <TabsContent value="notes" className="mt-0">
              <VideoNotesPanel
                video={activeVideo}
                token={token}
                currentTimestamp={currentPlaybackTime}
                onSeek={handleSeek}
              />
            </TabsContent>
          </Tabs>

          <LessonRail
            modules={modules}
            activeVideoId={activeVideo?.id ?? null}
            onSelectVideo={handleSelectVideo}
          />
        </main>

        <CurriculumSidebar
          modules={modules}
          activeVideoId={activeVideo?.id ?? null}
          totalItems={videos.length}
          completedItems={selectedSpace.completed_count}
          progress={selectedSpace.progress}
          isLoading={isCurriculumLoading}
          error={curriculumError}
          onSelectVideo={handleSelectVideo}
        />
      </div>

      {followingVideo ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-24 right-4 z-30 lg:bottom-6 lg:right-6"
        >
          <Button
            type="button"
            size="lg"
            onClick={handleContinue}
            className="min-w-0 px-4 shadow-premium sm:min-w-44 sm:px-5"
          >
            <span className="sm:hidden">Continue</span>
            <span className="hidden sm:inline">Continue Lesson</span>
            <ArrowRight />
          </Button>
        </motion.div>
      ) : null}
    </div>
  );
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
