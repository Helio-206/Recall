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

export type TranscriptSegment = {
  id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  text: string;
  order_index: number;
  created_at: ISODateString;
};

export type TranscriptJob = {
  id: string;
  user_id: string;
  video_id: string;
  status: ProcessingStatus;
  payload: {
    phase?: string;
    video_url?: string;
    segments_count?: number;
    model?: string;
    method?: "youtube_captions" | "youtube_auto_captions" | "whisper";
    language?: string;
  };
  error_message: string | null;
  attempts: number;
  started_at: ISODateString | null;
  finished_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
};

export type VideoTranscript = {
  video_id: string;
  status: ProcessingStatus;
  segments: TranscriptSegment[];
  job: TranscriptJob | null;
  error_message: string | null;
};

export type AISummary = {
  id: string;
  video_id: string;
  short_summary: string | null;
  detailed_summary: string | null;
  learning_notes: string | null;
  status: ProcessingStatus;
  prompt_version: string;
  created_at: ISODateString;
  updated_at: ISODateString;
};

export type KeyConcept = {
  id: string;
  video_id: string;
  concept: string;
  relevance_score: number;
};

export type KeyTakeaway = {
  id: string;
  video_id: string;
  content: string;
  order_index: number;
};

export type ReviewQuestion = {
  id: string;
  video_id: string;
  question: string;
  answer: string;
  order_index: number;
};

export type ImportantMoment = {
  id: string;
  video_id: string;
  title: string;
  timestamp: number;
  description: string;
  order_index: number;
};

export type AISummaryJob = {
  id: string;
  user_id: string;
  video_id: string;
  status: ProcessingStatus;
  payload: {
    phase?: string;
    video_title?: string;
    prompt_version?: string;
    provider?: string;
    chunk_count?: number;
  };
  error_message: string | null;
  attempts: number;
  started_at: ISODateString | null;
  finished_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
};

export type VideoLearningInsights = {
  video_id: string;
  status: ProcessingStatus;
  summary: AISummary | null;
  key_concepts: KeyConcept[];
  key_takeaways: KeyTakeaway[];
  review_questions: ReviewQuestion[];
  important_moments: ImportantMoment[];
  job: AISummaryJob | null;
  error_message: string | null;
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

export type VideoNote = {
  id: string;
  user_id: string;
  video_id: string;
  title: string | null;
  content: string;
  anchor_timestamp: number | null;
  created_at: ISODateString;
  updated_at: ISODateString;
};

export type VideoNoteUpsert = {
  title?: string | null;
  content: string;
  anchor_timestamp?: number | null;
};

export type SearchKind =
  | "all"
  | "transcript"
  | "note"
  | "summary"
  | "concept"
  | "important_moment";

export type SearchQuery = {
  id: string;
  query: string;
  last_used_at: ISODateString;
  use_count: number;
};

export type SearchResult = {
  id: string;
  kind: SearchKind;
  video_id: string;
  video_title: string;
  space_id: string;
  space_title: string;
  timestamp: number | null;
  title: string;
  excerpt: string;
  highlighted_excerpt: string;
  target_tab: "transcript" | "ai-summary" | "notes";
  relevance_score: number;
};

export type SearchResponse = {
  query: string;
  kind: SearchKind;
  page: number;
  per_page: number;
  total: number;
  hits: SearchResult[];
};

export type SearchQueryCreate = {
  query: string;
};

export type SearchResultClickPayload = {
  query: string;
  result_kind: string;
  result_id: string;
  space_id: string | null;
  video_id: string | null;
  timestamp: number | null;
};

export const RECALL_COLORS = {
  background: "#0A0A0F",
  surface: "#111117",
  border: "#1F1F2A",
  primary: "#2F6BFF",
  warm: "#FFB457",
  textPrimary: "#F5F7FA",
  textSecondary: "#A1A8B3",
} as const;
