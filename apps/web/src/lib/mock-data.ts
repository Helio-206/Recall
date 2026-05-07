import type { ActivityItem } from "@recall/shared";

export const starterActivity: ActivityItem[] = [
  {
    id: "activity-1",
    label: "DevOps Engineering",
    detail: "Linux File Permissions marked complete",
    created_at: new Date().toISOString(),
  },
  {
    id: "activity-2",
    label: "System Design",
    detail: "A new video was organized into the curriculum",
    created_at: new Date(Date.now() - 1000 * 60 * 48).toISOString(),
  },
  {
    id: "activity-3",
    label: "React Mastery",
    detail: "Learning path progress updated",
    created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
  },
];
