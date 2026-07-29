CREATE INDEX IF NOT EXISTS ix_extension_save_events_ingestion_job_id
  ON public.extension_save_events (ingestion_job_id);
CREATE INDEX IF NOT EXISTS ix_extension_save_events_source_id
  ON public.extension_save_events (source_id);
CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_source_id
  ON public.ingestion_jobs (source_id);
CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_space_id
  ON public.ingestion_jobs (space_id);
CREATE INDEX IF NOT EXISTS ix_search_result_clicks_space_id
  ON public.search_result_clicks (space_id);
CREATE INDEX IF NOT EXISTS ix_search_result_clicks_video_id
  ON public.search_result_clicks (video_id);

UPDATE public.alembic_version
SET version_num = '202607290001';
