const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtu.be",
]);

export function classifyPage(context) {
  const { url, hasEmbeddedVideo = false } = context;

  if (!url) {
    return unsupported("No active page was detected yet.", "web", "page");
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(url);
  } catch {
    return unsupported("This page is not a valid public URL.", "web", "page");
  }

  const host = parsedUrl.hostname.toLowerCase();
  const path = parsedUrl.pathname.replace(/^\/+/, "");
  const sourceType = detectYouTubeSourceType(parsedUrl, path);

  if (YOUTUBE_HOSTS.has(host)) {
    return {
      platform: "youtube",
      sourceType,
      supported: true,
      label: youtubeLabel(sourceType),
      reason: "Ready to save",
    };
  }

  if (["x.com", "twitter.com", "mobile.twitter.com"].includes(host)) {
    return unsupported("X/Twitter support is next in line.", "x", "post");
  }

  if (host.endsWith("tiktok.com")) {
    return unsupported("TikTok support is planned but not enabled yet.", "tiktok", "short_video");
  }

  if (host.endsWith("instagram.com")) {
    return unsupported("Instagram Reels support is planned but not enabled yet.", "instagram", "reel");
  }

  if (host === "vimeo.com" || host.endsWith(".vimeo.com")) {
    return unsupported("Vimeo support is planned but not enabled yet.", "vimeo", "video");
  }

  if (hasEmbeddedVideo) {
    return unsupported(
      "Embedded video detected. Generic web capture is prepared but not active yet.",
      "web",
      "embedded_video",
    );
  }

  return unsupported("This page is not supported yet.", "web", "page");
}

function detectYouTubeSourceType(parsedUrl, path) {
  if (parsedUrl.searchParams.has("list") || path.startsWith("playlist")) {
    return "playlist";
  }

  if (
    path.startsWith("@") ||
    path.startsWith("channel/") ||
    path.startsWith("c/") ||
    path.startsWith("user/")
  ) {
    return "channel";
  }

  return "single_video";
}

function youtubeLabel(sourceType) {
  if (sourceType === "playlist") {
    return "YouTube playlist";
  }
  if (sourceType === "channel") {
    return "YouTube channel";
  }
  return "YouTube video";
}

function unsupported(reason, platform, sourceType) {
  return {
    platform,
    sourceType,
    supported: false,
    label: "Unsupported for now",
    reason,
  };
}