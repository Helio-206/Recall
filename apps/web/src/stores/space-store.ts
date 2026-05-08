"use client";

import type {
  CurriculumManualOverrideUpdate,
  CurriculumReconstructionJob,
  CurriculumReconstructionRequest,
  RecallSpace,
  RecallVideo,
  SpaceCurriculum,
} from "@recall/shared";
import { create } from "zustand";

import { apiFetch } from "@/lib/api";

type SpacePayload = {
  title: string;
  description?: string;
  topic?: string;
};

type VideoPayload = {
  url: string;
  title?: string;
};

type CurriculumState = {
  selectedCurriculum: SpaceCurriculum | null;
  isCurriculumLoading: boolean;
  curriculumError: string | null;
};

type SpaceState = CurriculumState & {
  spaces: RecallSpace[];
  selectedSpace: RecallSpace | null;
  isLoading: boolean;
  error: string | null;
  fetchSpaces: (token: string) => Promise<void>;
  fetchSpace: (token: string, id: string) => Promise<void>;
  fetchCurriculum: (token: string, id: string) => Promise<void>;
  createSpace: (token: string, payload: SpacePayload) => Promise<RecallSpace>;
  addVideo: (token: string, spaceId: string, payload: VideoPayload) => Promise<RecallVideo>;
  updateVideo: (token: string, videoId: string, payload: Partial<RecallVideo>) => Promise<RecallVideo>;
  rebuildCurriculum: (
    token: string,
    spaceId: string,
    payload?: CurriculumReconstructionRequest,
  ) => Promise<CurriculumReconstructionJob>;
  updateCurriculumOverride: (
    token: string,
    spaceId: string,
    videoId: string,
    payload: CurriculumManualOverrideUpdate,
  ) => Promise<SpaceCurriculum>;
  clearSelected: () => void;
};

export const useSpaceStore = create<SpaceState>((set, get) => ({
  spaces: [],
  selectedSpace: null,
  selectedCurriculum: null,
  isLoading: false,
  isCurriculumLoading: false,
  error: null,
  curriculumError: null,

  fetchSpaces: async (token) => {
    set({ isLoading: true, error: null });
    try {
      const spaces = await apiFetch<RecallSpace[]>("/spaces", { token });
      set({ spaces, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unable to load spaces.", isLoading: false });
    }
  },

  fetchSpace: async (token, id) => {
    set({ isLoading: true, error: null });
    try {
      const selectedSpace = await apiFetch<RecallSpace>(`/spaces/${id}`, { token });
      set({ selectedSpace, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unable to load this space.", isLoading: false });
    }
  },

  fetchCurriculum: async (token, id) => {
    set({ isCurriculumLoading: true, curriculumError: null });
    try {
      const selectedCurriculum = await apiFetch<SpaceCurriculum>(`/spaces/${id}/curriculum`, {
        token,
      });
      set({ selectedCurriculum, isCurriculumLoading: false });
    } catch (error) {
      set({
        curriculumError: error instanceof Error ? error.message : "Unable to load the curriculum.",
        isCurriculumLoading: false,
      });
    }
  },

  createSpace: async (token, payload) => {
    const space = await apiFetch<RecallSpace>("/spaces", {
      token,
      method: "POST",
      body: JSON.stringify(payload),
    });
    set({ spaces: [space, ...get().spaces] });
    return space;
  },

  addVideo: async (token, spaceId, payload) => {
    const video = await apiFetch<RecallVideo>(`/spaces/${spaceId}/videos`, {
      token,
      method: "POST",
      body: JSON.stringify(payload),
    });
    const selectedSpace = get().selectedSpace;
    if (selectedSpace?.id === spaceId) {
      const videos = [...(selectedSpace.videos ?? []), video];
      const completedCount = videos.filter((item) => item.completed).length;
      const progress = videos.length ? Math.round((completedCount / videos.length) * 100) : 0;
      set({
        selectedSpace: {
          ...selectedSpace,
          videos,
          video_count: videos.length,
          completed_count: completedCount,
          progress,
        },
      });
    }
    if (get().selectedCurriculum?.space_id === spaceId) {
      set({ selectedCurriculum: null });
    }
    set({
      spaces: get().spaces.map((space) => {
        if (space.id !== spaceId) return space;
        const videoCount = space.video_count + 1;
        const completedCount = space.completed_count + (video.completed ? 1 : 0);
        return {
          ...space,
          video_count: videoCount,
          completed_count: completedCount,
          progress: videoCount ? Math.round((completedCount / videoCount) * 100) : 0,
        };
      }),
    });
    return video;
  },

  updateVideo: async (token, videoId, payload) => {
    const video = await apiFetch<RecallVideo>(`/videos/${videoId}`, {
      token,
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    const selectedSpace = get().selectedSpace;
    let nextProgress = selectedSpace?.progress ?? 0;
    let nextCompletedCount = selectedSpace?.completed_count ?? 0;
    if (selectedSpace) {
      const videos = (selectedSpace.videos ?? []).map((item) => (item.id === video.id ? video : item));
      nextCompletedCount = videos.filter((item) => item.completed).length;
      nextProgress = videos.length ? Math.round((nextCompletedCount / videos.length) * 100) : 0;
      set({
        selectedSpace: {
          ...selectedSpace,
          videos,
          completed_count: nextCompletedCount,
          progress: nextProgress,
        },
      });
    }
    if (get().selectedCurriculum?.space_id === video.space_id) {
      set({ selectedCurriculum: null });
    }
    set({
      spaces: get().spaces.map((space) => {
        if (space.id !== video.space_id || selectedSpace?.id !== video.space_id) {
          return space;
        }
        return {
          ...space,
          completed_count: nextCompletedCount,
          progress: nextProgress,
        };
      }),
    });
    return video;
  },

  rebuildCurriculum: async (token, spaceId, payload = {}) => {
    const job = await apiFetch<CurriculumReconstructionJob>(`/spaces/${spaceId}/curriculum/rebuild`, {
      token,
      method: "POST",
      body: JSON.stringify(payload),
    });
    const current = get().selectedCurriculum;
    if (current?.space_id === spaceId) {
      set({
        selectedCurriculum: {
          ...current,
          latest_job: job,
        },
      });
    }
    return job;
  },

  updateCurriculumOverride: async (token, spaceId, videoId, payload) => {
    const selectedCurriculum = await apiFetch<SpaceCurriculum>(
      `/spaces/${spaceId}/curriculum/videos/${videoId}/override`,
      {
        token,
        method: "PATCH",
        body: JSON.stringify(payload),
      },
    );
    set({ selectedCurriculum, curriculumError: null });
    return selectedCurriculum;
  },

  clearSelected: () => set({ selectedSpace: null, selectedCurriculum: null }),
}));
