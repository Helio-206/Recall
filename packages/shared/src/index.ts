export type ISODateString = string;

export type RecallUser = {
  id: string;
  name: string;
  email: string;
  created_at: ISODateString;
};

export type RecallVideo = {
  id: string;
  source_id: string | null;
  title: string;
  thumbnail: string | null;
  author: string | null;
  duration: number | null;
  url: string;
  order_index: number;
  completed: boolean;
  metadata_status: ProcessingStatus;
  transcript_status: ProcessingStatus;
  processing_status: ProcessingStatus;
  space_id: string;
  created_at: ISODateString;
  updated_at: ISODateString;
};

export type ProcessingStatus = "pending" | "processing" | "completed" | "failed";

export type SourceType = "single_video" | "playlist" | "channel";

export type RecallSource = {
  id: string;
  user_id: string;
  space_id: string;
  url: string;
  platform: "youtube";
  source_type: SourceType;
  title: string | null;
  author: string | null;
  thumbnail: string | null;
  duration: number | null;
  status: ProcessingStatus;
  error_message: string | null;
  created_at: ISODateString;
  updated_at: ISODateString;
};

export type IngestionJob = {
  id: string;
  user_id: string;
  space_id: string;
  source_id: string;
  type: string;
  status: ProcessingStatus;
  payload: {
    url?: string;
    title_override?: string | null;
    source_type?: SourceType;
    phase?: string;
    detected_count?: number;
    added_count?: number;
    duplicate_count?: number;
    skipped_count?: number;
  };
  error_message: string | null;
  attempts: number;
  started_at: ISODateString | null;
  finished_at: ISODateString | null;
  created_at: ISODateString;
};

export type IngestionAccepted = {
  job_id: string;
  source_id: string;
  status: ProcessingStatus;
};

export type RecallSpace = {
  id: string;
  title: string;
  description: string | null;
  topic: string | null;
  created_at: ISODateString;
  updated_at: ISODateString;
  user_id: string;
  progress: number;
  video_count: number;
  completed_count: number;
  videos?: RecallVideo[];
};

export type AuthSession = {
  access_token: string;
  token_type: "bearer";
  user: RecallUser;
};

export type ActivityItem = {
  id: string;
  label: string;
  detail: string;
  created_at: ISODateString;
};

export const RECALL_COLORS = {
  background: "#0A0A0F",
  surface: "#111117",
  border: "#1F1F2A",
  primary: "#2F6BFF",
  warm: "#FFB457",
  textPrimary: "#F5F7FA",
  textSecondary: "#A1A8B3"
} as const;
