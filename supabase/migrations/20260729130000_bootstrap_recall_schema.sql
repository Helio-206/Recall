--
-- PostgreSQL database dump
--


-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--



--
-- Name: SCHEMA "public"; Type: COMMENT; Schema: -; Owner: -
--



SET default_tablespace = '';

SET default_table_access_method = "heap";

--
-- Name: ai_summaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."ai_summaries" (
    "video_id" "uuid" NOT NULL,
    "short_summary" "text",
    "detailed_summary" "text",
    "learning_notes" "text",
    "status" character varying(40) NOT NULL,
    "prompt_version" character varying(40) NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: ai_summary_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."ai_summary_jobs" (
    "user_id" "uuid" NOT NULL,
    "video_id" "uuid" NOT NULL,
    "status" character varying(40) NOT NULL,
    "payload" "jsonb" NOT NULL,
    "error_message" "text",
    "attempts" integer NOT NULL,
    "started_at" timestamp with time zone,
    "finished_at" timestamp with time zone,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."alembic_version" (
    "version_num" character varying(32) NOT NULL
);


--
-- Name: curriculum_reconstruction_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."curriculum_reconstruction_jobs" (
    "user_id" "uuid" NOT NULL,
    "space_id" "uuid" NOT NULL,
    "status" character varying(40) NOT NULL,
    "provider" character varying(40) NOT NULL,
    "model" character varying(160) NOT NULL,
    "prompt_version" character varying(40) NOT NULL,
    "payload" "jsonb" NOT NULL,
    "error_message" "text",
    "attempts" integer NOT NULL,
    "started_at" timestamp with time zone,
    "finished_at" timestamp with time zone,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: extension_save_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."extension_save_events" (
    "user_id" "uuid" NOT NULL,
    "space_id" "uuid" NOT NULL,
    "source_id" "uuid",
    "ingestion_job_id" "uuid",
    "url" "text" NOT NULL,
    "normalized_url" "text" NOT NULL,
    "platform" character varying(40) NOT NULL,
    "source_type" character varying(40) NOT NULL,
    "status" character varying(40) NOT NULL,
    "page_title" character varying(220),
    "page_description" character varying(500),
    "browser" character varying(40),
    "extension_version" character varying(40),
    "page_metadata" "jsonb" NOT NULL,
    "error_message" "text",
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: important_moments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."important_moments" (
    "video_id" "uuid" NOT NULL,
    "title" character varying(220) NOT NULL,
    "timestamp" double precision NOT NULL,
    "description" "text" NOT NULL,
    "order_index" integer NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: ingestion_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."ingestion_jobs" (
    "user_id" "uuid" NOT NULL,
    "space_id" "uuid" NOT NULL,
    "source_id" "uuid" NOT NULL,
    "type" character varying(40) NOT NULL,
    "status" character varying(40) NOT NULL,
    "payload" "jsonb" NOT NULL,
    "error_message" "text",
    "attempts" integer NOT NULL,
    "started_at" timestamp with time zone,
    "finished_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "id" "uuid" NOT NULL
);


--
-- Name: key_concepts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."key_concepts" (
    "video_id" "uuid" NOT NULL,
    "concept" character varying(220) NOT NULL,
    "relevance_score" double precision NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: key_takeaways; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."key_takeaways" (
    "video_id" "uuid" NOT NULL,
    "content" "text" NOT NULL,
    "order_index" integer NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: learning_modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."learning_modules" (
    "space_id" "uuid" NOT NULL,
    "reconstruction_job_id" "uuid",
    "title" character varying(180) NOT NULL,
    "description" "text",
    "order_index" integer NOT NULL,
    "difficulty_level" character varying(24) NOT NULL,
    "learning_objectives" "jsonb" NOT NULL,
    "estimated_duration_minutes" integer,
    "rationale" "text",
    "confidence_score" double precision NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: learning_spaces; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."learning_spaces" (
    "title" character varying(160) NOT NULL,
    "description" "text",
    "topic" character varying(120),
    "user_id" "uuid" NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: module_videos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."module_videos" (
    "module_id" "uuid" NOT NULL,
    "video_id" "uuid" NOT NULL,
    "order_index" integer NOT NULL,
    "rationale" "text",
    "confidence_score" double precision NOT NULL,
    "is_manual_override" boolean NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: review_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."review_questions" (
    "video_id" "uuid" NOT NULL,
    "question" "text" NOT NULL,
    "answer" "text" NOT NULL,
    "order_index" integer NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: search_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."search_queries" (
    "user_id" "uuid" NOT NULL,
    "query" character varying(220) NOT NULL,
    "last_used_at" timestamp with time zone NOT NULL,
    "use_count" integer NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: search_result_clicks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."search_result_clicks" (
    "user_id" "uuid" NOT NULL,
    "query" character varying(220) NOT NULL,
    "result_kind" character varying(40) NOT NULL,
    "result_id" character varying(120) NOT NULL,
    "space_id" "uuid",
    "video_id" "uuid",
    "timestamp" double precision,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."sources" (
    "user_id" "uuid" NOT NULL,
    "space_id" "uuid" NOT NULL,
    "url" "text" NOT NULL,
    "platform" character varying(40) NOT NULL,
    "source_type" character varying(40) NOT NULL,
    "title" character varying(300),
    "author" character varying(180),
    "thumbnail" "text",
    "duration" integer,
    "status" character varying(40) NOT NULL,
    "error_message" "text",
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: transcript_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."transcript_jobs" (
    "user_id" "uuid" NOT NULL,
    "video_id" "uuid" NOT NULL,
    "status" character varying(40) NOT NULL,
    "payload" "jsonb" NOT NULL,
    "error_message" "text",
    "attempts" integer NOT NULL,
    "started_at" timestamp with time zone,
    "finished_at" timestamp with time zone,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: transcript_segments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."transcript_segments" (
    "video_id" "uuid" NOT NULL,
    "start_time" double precision NOT NULL,
    "end_time" double precision NOT NULL,
    "text" "text" NOT NULL,
    "order_index" integer NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."users" (
    "name" character varying(120) NOT NULL,
    "email" character varying(255) NOT NULL,
    "password_hash" character varying(255) NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: video_curriculum_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."video_curriculum_profiles" (
    "space_id" "uuid" NOT NULL,
    "video_id" "uuid" NOT NULL,
    "primary_topic" character varying(180) NOT NULL,
    "subtopics" "jsonb" NOT NULL,
    "difficulty_level" character varying(24) NOT NULL,
    "prerequisite_topics" "jsonb" NOT NULL,
    "extracted_keywords" "jsonb" NOT NULL,
    "module_hint" character varying(180),
    "redundancy_signals" "jsonb" NOT NULL,
    "estimated_sequence_score" double precision NOT NULL,
    "confidence_score" double precision NOT NULL,
    "rationale" "text",
    "provider" character varying(40) NOT NULL,
    "model" character varying(160) NOT NULL,
    "prompt_version" character varying(40) NOT NULL,
    "manual_module_title" character varying(180),
    "manual_order_index" integer,
    "manual_override_locked" boolean NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: video_dependencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."video_dependencies" (
    "space_id" "uuid" NOT NULL,
    "prerequisite_video_id" "uuid" NOT NULL,
    "dependent_video_id" "uuid" NOT NULL,
    "dependency_type" character varying(40) NOT NULL,
    "rationale" "text",
    "confidence_score" double precision NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: video_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."video_notes" (
    "user_id" "uuid" NOT NULL,
    "video_id" "uuid" NOT NULL,
    "title" character varying(180),
    "content" "text" NOT NULL,
    "anchor_timestamp" double precision,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


--
-- Name: videos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."videos" (
    "title" character varying(220) NOT NULL,
    "thumbnail" "text",
    "author" character varying(160),
    "duration" integer,
    "url" "text" NOT NULL,
    "order_index" integer NOT NULL,
    "completed" boolean NOT NULL,
    "space_id" "uuid" NOT NULL,
    "id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "source_id" "uuid",
    "metadata_status" character varying(40) DEFAULT 'completed'::character varying NOT NULL,
    "transcript_status" character varying(40) DEFAULT 'pending'::character varying NOT NULL,
    "processing_status" character varying(40) DEFAULT 'completed'::character varying NOT NULL
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."alembic_version"
    ADD CONSTRAINT "alembic_version_pkc" PRIMARY KEY ("version_num");


--
-- Name: ai_summaries pk_ai_summaries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ai_summaries"
    ADD CONSTRAINT "pk_ai_summaries" PRIMARY KEY ("id");


--
-- Name: ai_summary_jobs pk_ai_summary_jobs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ai_summary_jobs"
    ADD CONSTRAINT "pk_ai_summary_jobs" PRIMARY KEY ("id");


--
-- Name: curriculum_reconstruction_jobs pk_curriculum_reconstruction_jobs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."curriculum_reconstruction_jobs"
    ADD CONSTRAINT "pk_curriculum_reconstruction_jobs" PRIMARY KEY ("id");


--
-- Name: extension_save_events pk_extension_save_events; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."extension_save_events"
    ADD CONSTRAINT "pk_extension_save_events" PRIMARY KEY ("id");


--
-- Name: important_moments pk_important_moments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."important_moments"
    ADD CONSTRAINT "pk_important_moments" PRIMARY KEY ("id");


--
-- Name: ingestion_jobs pk_ingestion_jobs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ingestion_jobs"
    ADD CONSTRAINT "pk_ingestion_jobs" PRIMARY KEY ("id");


--
-- Name: key_concepts pk_key_concepts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."key_concepts"
    ADD CONSTRAINT "pk_key_concepts" PRIMARY KEY ("id");


--
-- Name: key_takeaways pk_key_takeaways; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."key_takeaways"
    ADD CONSTRAINT "pk_key_takeaways" PRIMARY KEY ("id");


--
-- Name: learning_modules pk_learning_modules; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."learning_modules"
    ADD CONSTRAINT "pk_learning_modules" PRIMARY KEY ("id");


--
-- Name: learning_spaces pk_learning_spaces; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."learning_spaces"
    ADD CONSTRAINT "pk_learning_spaces" PRIMARY KEY ("id");


--
-- Name: module_videos pk_module_videos; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."module_videos"
    ADD CONSTRAINT "pk_module_videos" PRIMARY KEY ("id");


--
-- Name: review_questions pk_review_questions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."review_questions"
    ADD CONSTRAINT "pk_review_questions" PRIMARY KEY ("id");


--
-- Name: search_queries pk_search_queries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_queries"
    ADD CONSTRAINT "pk_search_queries" PRIMARY KEY ("id");


--
-- Name: search_result_clicks pk_search_result_clicks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_result_clicks"
    ADD CONSTRAINT "pk_search_result_clicks" PRIMARY KEY ("id");


--
-- Name: sources pk_sources; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."sources"
    ADD CONSTRAINT "pk_sources" PRIMARY KEY ("id");


--
-- Name: transcript_jobs pk_transcript_jobs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."transcript_jobs"
    ADD CONSTRAINT "pk_transcript_jobs" PRIMARY KEY ("id");


--
-- Name: transcript_segments pk_transcript_segments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."transcript_segments"
    ADD CONSTRAINT "pk_transcript_segments" PRIMARY KEY ("id");


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "pk_users" PRIMARY KEY ("id");


--
-- Name: video_curriculum_profiles pk_video_curriculum_profiles; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_curriculum_profiles"
    ADD CONSTRAINT "pk_video_curriculum_profiles" PRIMARY KEY ("id");


--
-- Name: video_dependencies pk_video_dependencies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_dependencies"
    ADD CONSTRAINT "pk_video_dependencies" PRIMARY KEY ("id");


--
-- Name: video_notes pk_video_notes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_notes"
    ADD CONSTRAINT "pk_video_notes" PRIMARY KEY ("id");


--
-- Name: videos pk_videos; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."videos"
    ADD CONSTRAINT "pk_videos" PRIMARY KEY ("id");


--
-- Name: ai_summaries uq_ai_summaries_video_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ai_summaries"
    ADD CONSTRAINT "uq_ai_summaries_video_id" UNIQUE ("video_id");


--
-- Name: learning_modules uq_learning_modules_space_order; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."learning_modules"
    ADD CONSTRAINT "uq_learning_modules_space_order" UNIQUE ("space_id", "order_index");


--
-- Name: module_videos uq_module_videos_module_order; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."module_videos"
    ADD CONSTRAINT "uq_module_videos_module_order" UNIQUE ("module_id", "order_index");


--
-- Name: module_videos uq_module_videos_module_video; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."module_videos"
    ADD CONSTRAINT "uq_module_videos_module_video" UNIQUE ("module_id", "video_id");


--
-- Name: search_queries uq_search_queries_user_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_queries"
    ADD CONSTRAINT "uq_search_queries_user_id" UNIQUE ("user_id", "query");


--
-- Name: video_curriculum_profiles uq_video_curriculum_profiles_video_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_curriculum_profiles"
    ADD CONSTRAINT "uq_video_curriculum_profiles_video_id" UNIQUE ("video_id");


--
-- Name: video_dependencies uq_video_dependencies_edge; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_dependencies"
    ADD CONSTRAINT "uq_video_dependencies_edge" UNIQUE ("prerequisite_video_id", "dependent_video_id");


--
-- Name: video_notes uq_video_notes_user_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_notes"
    ADD CONSTRAINT "uq_video_notes_user_id" UNIQUE ("user_id", "video_id");


--
-- Name: ix_ai_summaries_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ai_summaries_status" ON "public"."ai_summaries" USING "btree" ("status");


--
-- Name: ix_ai_summary_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ai_summary_jobs_status" ON "public"."ai_summary_jobs" USING "btree" ("status");


--
-- Name: ix_ai_summary_jobs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ai_summary_jobs_user_id" ON "public"."ai_summary_jobs" USING "btree" ("user_id");


--
-- Name: ix_ai_summary_jobs_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ai_summary_jobs_video_id" ON "public"."ai_summary_jobs" USING "btree" ("video_id");


--
-- Name: ix_curriculum_reconstruction_jobs_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_curriculum_reconstruction_jobs_space_id" ON "public"."curriculum_reconstruction_jobs" USING "btree" ("space_id");


--
-- Name: ix_curriculum_reconstruction_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_curriculum_reconstruction_jobs_status" ON "public"."curriculum_reconstruction_jobs" USING "btree" ("status");


--
-- Name: ix_curriculum_reconstruction_jobs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_curriculum_reconstruction_jobs_user_id" ON "public"."curriculum_reconstruction_jobs" USING "btree" ("user_id");


--
-- Name: ix_extension_save_events_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_extension_save_events_space_id" ON "public"."extension_save_events" USING "btree" ("space_id");


--
-- Name: ix_extension_save_events_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_extension_save_events_status" ON "public"."extension_save_events" USING "btree" ("status");


--
-- Name: ix_extension_save_events_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_extension_save_events_user_created" ON "public"."extension_save_events" USING "btree" ("user_id", "created_at");


--
-- Name: ix_important_moments_video_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_important_moments_video_timestamp" ON "public"."important_moments" USING "btree" ("video_id", "timestamp");


--
-- Name: ix_ingestion_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ingestion_jobs_status" ON "public"."ingestion_jobs" USING "btree" ("status");


--
-- Name: ix_ingestion_jobs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ingestion_jobs_user_id" ON "public"."ingestion_jobs" USING "btree" ("user_id");


--
-- Name: ix_key_concepts_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_key_concepts_video_id" ON "public"."key_concepts" USING "btree" ("video_id");


--
-- Name: ix_key_takeaways_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_key_takeaways_video_id" ON "public"."key_takeaways" USING "btree" ("video_id");


--
-- Name: ix_learning_modules_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_learning_modules_job_id" ON "public"."learning_modules" USING "btree" ("reconstruction_job_id");


--
-- Name: ix_learning_modules_space_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_learning_modules_space_difficulty" ON "public"."learning_modules" USING "btree" ("space_id", "difficulty_level");


--
-- Name: ix_learning_modules_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_learning_modules_space_id" ON "public"."learning_modules" USING "btree" ("space_id");


--
-- Name: ix_learning_spaces_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_learning_spaces_user_created" ON "public"."learning_spaces" USING "btree" ("user_id", "created_at");


--
-- Name: ix_learning_spaces_user_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_learning_spaces_user_topic" ON "public"."learning_spaces" USING "btree" ("user_id", "topic");


--
-- Name: ix_module_videos_module_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_module_videos_module_id" ON "public"."module_videos" USING "btree" ("module_id");


--
-- Name: ix_module_videos_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_module_videos_video_id" ON "public"."module_videos" USING "btree" ("video_id");


--
-- Name: ix_review_questions_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_review_questions_video_id" ON "public"."review_questions" USING "btree" ("video_id");


--
-- Name: ix_search_queries_last_used_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_search_queries_last_used_at" ON "public"."search_queries" USING "btree" ("last_used_at");


--
-- Name: ix_search_queries_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_search_queries_user_id" ON "public"."search_queries" USING "btree" ("user_id");


--
-- Name: ix_search_result_clicks_result_kind; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_search_result_clicks_result_kind" ON "public"."search_result_clicks" USING "btree" ("result_kind");


--
-- Name: ix_search_result_clicks_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_search_result_clicks_user_id" ON "public"."search_result_clicks" USING "btree" ("user_id");


--
-- Name: ix_sources_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_sources_space_id" ON "public"."sources" USING "btree" ("space_id");


--
-- Name: ix_sources_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_sources_status" ON "public"."sources" USING "btree" ("status");


--
-- Name: ix_sources_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_sources_user_id" ON "public"."sources" USING "btree" ("user_id");


--
-- Name: ix_transcript_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_transcript_jobs_status" ON "public"."transcript_jobs" USING "btree" ("status");


--
-- Name: ix_transcript_jobs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_transcript_jobs_user_id" ON "public"."transcript_jobs" USING "btree" ("user_id");


--
-- Name: ix_transcript_jobs_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_transcript_jobs_video_id" ON "public"."transcript_jobs" USING "btree" ("video_id");


--
-- Name: ix_transcript_segments_video_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_transcript_segments_video_order" ON "public"."transcript_segments" USING "btree" ("video_id", "order_index");


--
-- Name: ix_transcript_segments_video_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_transcript_segments_video_start" ON "public"."transcript_segments" USING "btree" ("video_id", "start_time");


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_users_email" ON "public"."users" USING "btree" ("email");


--
-- Name: ix_video_curriculum_profiles_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_curriculum_profiles_difficulty" ON "public"."video_curriculum_profiles" USING "btree" ("difficulty_level");


--
-- Name: ix_video_curriculum_profiles_primary_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_curriculum_profiles_primary_topic" ON "public"."video_curriculum_profiles" USING "btree" ("primary_topic");


--
-- Name: ix_video_curriculum_profiles_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_curriculum_profiles_space_id" ON "public"."video_curriculum_profiles" USING "btree" ("space_id");


--
-- Name: ix_video_dependencies_dependent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_dependencies_dependent" ON "public"."video_dependencies" USING "btree" ("dependent_video_id");


--
-- Name: ix_video_dependencies_prerequisite; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_dependencies_prerequisite" ON "public"."video_dependencies" USING "btree" ("prerequisite_video_id");


--
-- Name: ix_video_dependencies_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_dependencies_space_id" ON "public"."video_dependencies" USING "btree" ("space_id");


--
-- Name: ix_video_notes_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_notes_user_id" ON "public"."video_notes" USING "btree" ("user_id");


--
-- Name: ix_video_notes_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_video_notes_video_id" ON "public"."video_notes" USING "btree" ("video_id");


--
-- Name: ix_videos_source_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_videos_source_id" ON "public"."videos" USING "btree" ("source_id");


--
-- Name: ix_videos_space_completed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_videos_space_completed" ON "public"."videos" USING "btree" ("space_id", "completed");


--
-- Name: ix_videos_space_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_videos_space_order" ON "public"."videos" USING "btree" ("space_id", "order_index");


--
-- Name: ix_videos_url; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_videos_url" ON "public"."videos" USING "btree" ("url");


--
-- Name: ai_summaries fk_ai_summaries_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ai_summaries"
    ADD CONSTRAINT "fk_ai_summaries_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: ai_summary_jobs fk_ai_summary_jobs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ai_summary_jobs"
    ADD CONSTRAINT "fk_ai_summary_jobs_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: ai_summary_jobs fk_ai_summary_jobs_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ai_summary_jobs"
    ADD CONSTRAINT "fk_ai_summary_jobs_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: curriculum_reconstruction_jobs fk_curriculum_reconstruction_jobs_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."curriculum_reconstruction_jobs"
    ADD CONSTRAINT "fk_curriculum_reconstruction_jobs_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: curriculum_reconstruction_jobs fk_curriculum_reconstruction_jobs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."curriculum_reconstruction_jobs"
    ADD CONSTRAINT "fk_curriculum_reconstruction_jobs_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: extension_save_events fk_extension_save_events_ingestion_job_id_ingestion_jobs; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."extension_save_events"
    ADD CONSTRAINT "fk_extension_save_events_ingestion_job_id_ingestion_jobs" FOREIGN KEY ("ingestion_job_id") REFERENCES "public"."ingestion_jobs"("id") ON DELETE SET NULL;


--
-- Name: extension_save_events fk_extension_save_events_source_id_sources; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."extension_save_events"
    ADD CONSTRAINT "fk_extension_save_events_source_id_sources" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE SET NULL;


--
-- Name: extension_save_events fk_extension_save_events_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."extension_save_events"
    ADD CONSTRAINT "fk_extension_save_events_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: extension_save_events fk_extension_save_events_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."extension_save_events"
    ADD CONSTRAINT "fk_extension_save_events_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: important_moments fk_important_moments_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."important_moments"
    ADD CONSTRAINT "fk_important_moments_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: ingestion_jobs fk_ingestion_jobs_source_id_sources; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ingestion_jobs"
    ADD CONSTRAINT "fk_ingestion_jobs_source_id_sources" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE CASCADE;


--
-- Name: ingestion_jobs fk_ingestion_jobs_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ingestion_jobs"
    ADD CONSTRAINT "fk_ingestion_jobs_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: ingestion_jobs fk_ingestion_jobs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."ingestion_jobs"
    ADD CONSTRAINT "fk_ingestion_jobs_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: key_concepts fk_key_concepts_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."key_concepts"
    ADD CONSTRAINT "fk_key_concepts_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: key_takeaways fk_key_takeaways_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."key_takeaways"
    ADD CONSTRAINT "fk_key_takeaways_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: learning_modules fk_learning_modules_reconstruction_job_id_curriculum_re_ec45; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."learning_modules"
    ADD CONSTRAINT "fk_learning_modules_reconstruction_job_id_curriculum_re_ec45" FOREIGN KEY ("reconstruction_job_id") REFERENCES "public"."curriculum_reconstruction_jobs"("id") ON DELETE SET NULL;


--
-- Name: learning_modules fk_learning_modules_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."learning_modules"
    ADD CONSTRAINT "fk_learning_modules_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: learning_spaces fk_learning_spaces_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."learning_spaces"
    ADD CONSTRAINT "fk_learning_spaces_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: module_videos fk_module_videos_module_id_learning_modules; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."module_videos"
    ADD CONSTRAINT "fk_module_videos_module_id_learning_modules" FOREIGN KEY ("module_id") REFERENCES "public"."learning_modules"("id") ON DELETE CASCADE;


--
-- Name: module_videos fk_module_videos_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."module_videos"
    ADD CONSTRAINT "fk_module_videos_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: review_questions fk_review_questions_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."review_questions"
    ADD CONSTRAINT "fk_review_questions_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: search_queries fk_search_queries_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_queries"
    ADD CONSTRAINT "fk_search_queries_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: search_result_clicks fk_search_result_clicks_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_result_clicks"
    ADD CONSTRAINT "fk_search_result_clicks_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE SET NULL;


--
-- Name: search_result_clicks fk_search_result_clicks_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_result_clicks"
    ADD CONSTRAINT "fk_search_result_clicks_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: search_result_clicks fk_search_result_clicks_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."search_result_clicks"
    ADD CONSTRAINT "fk_search_result_clicks_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE SET NULL;


--
-- Name: sources fk_sources_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."sources"
    ADD CONSTRAINT "fk_sources_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: sources fk_sources_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."sources"
    ADD CONSTRAINT "fk_sources_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: transcript_jobs fk_transcript_jobs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."transcript_jobs"
    ADD CONSTRAINT "fk_transcript_jobs_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: transcript_jobs fk_transcript_jobs_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."transcript_jobs"
    ADD CONSTRAINT "fk_transcript_jobs_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: transcript_segments fk_transcript_segments_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."transcript_segments"
    ADD CONSTRAINT "fk_transcript_segments_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: video_curriculum_profiles fk_video_curriculum_profiles_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_curriculum_profiles"
    ADD CONSTRAINT "fk_video_curriculum_profiles_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: video_curriculum_profiles fk_video_curriculum_profiles_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_curriculum_profiles"
    ADD CONSTRAINT "fk_video_curriculum_profiles_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: video_dependencies fk_video_dependencies_dependent_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_dependencies"
    ADD CONSTRAINT "fk_video_dependencies_dependent_video_id_videos" FOREIGN KEY ("dependent_video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: video_dependencies fk_video_dependencies_prerequisite_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_dependencies"
    ADD CONSTRAINT "fk_video_dependencies_prerequisite_video_id_videos" FOREIGN KEY ("prerequisite_video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: video_dependencies fk_video_dependencies_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_dependencies"
    ADD CONSTRAINT "fk_video_dependencies_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- Name: video_notes fk_video_notes_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_notes"
    ADD CONSTRAINT "fk_video_notes_user_id_users" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;


--
-- Name: video_notes fk_video_notes_video_id_videos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."video_notes"
    ADD CONSTRAINT "fk_video_notes_video_id_videos" FOREIGN KEY ("video_id") REFERENCES "public"."videos"("id") ON DELETE CASCADE;


--
-- Name: videos fk_videos_source_id_sources; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."videos"
    ADD CONSTRAINT "fk_videos_source_id_sources" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE SET NULL;


--
-- Name: videos fk_videos_space_id_learning_spaces; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."videos"
    ADD CONSTRAINT "fk_videos_space_id_learning_spaces" FOREIGN KEY ("space_id") REFERENCES "public"."learning_spaces"("id") ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--



INSERT INTO public.alembic_version (version_num) VALUES ('202605080003');
