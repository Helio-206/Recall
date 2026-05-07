import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(totalSeconds?: number | null) {
  if (!totalSeconds) return "Queued";
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function formatShortDate(date: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
  }).format(new Date(date));
}

export function initials(name?: string | null) {
  if (!name) return "R";
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function getYouTubeVideoId(url: string) {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.replace("www.", "");

    if (host === "youtu.be") {
      return parsed.pathname.split("/").filter(Boolean)[0] ?? null;
    }

    if (host === "youtube.com" || host === "m.youtube.com" || host === "youtube-nocookie.com") {
      const watchId = parsed.searchParams.get("v");
      if (watchId) return watchId;

      const segments = parsed.pathname.split("/").filter(Boolean);
      if (segments[0] === "shorts" || segments[0] === "embed") {
        return segments[1] ?? null;
      }
    }
  } catch {
    return null;
  }

  return null;
}

export function getYouTubeEmbedUrl(url: string) {
  const videoId = getYouTubeVideoId(url);
  if (!videoId) return null;
  const params = new URLSearchParams({
    rel: "0",
    modestbranding: "1",
  });
  return `https://www.youtube-nocookie.com/embed/${videoId}?${params.toString()}`;
}
