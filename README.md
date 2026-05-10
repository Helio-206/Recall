# Recall

Turn video courses into a structured, searchable knowledge base. Add a YouTube video or playlist (or a Coursera course), and Recall transcribes it, builds a smart curriculum, lets you take notes and query the content with AI summaries.

---

## Table of contents

1. [Architecture overview](#architecture-overview)
2. [Repository structure](#repository-structure)
3. [How things fit together](#how-things-fit-together)
4. [Full ingestion workflow](#full-ingestion-workflow)
5. [Transcription workflow](#transcription-workflow)
6. [Curriculum reconstruction](#curriculum-reconstruction)
7. [AI summaries](#ai-summaries)
8. [Search](#search)
9. [Browser extension](#browser-extension)
10. [Authentication](#authentication)
11. [API reference](#api-reference)
12. [Running locally](#running-locally)
13. [Running with Docker](#running-with-docker)
14. [Environment variables](#environment-variables)
15. [Database migrations](#database-migrations)
16. [Tech stack](#tech-stack)

---

## Architecture overview

```
Browser / Extension
       │
       ▼
  Next.js (web)          ← Server-side proxy forwards /api/v1/* to the FastAPI backend
       │
       ▼
  FastAPI (api)          ← REST API, JWT auth, business logic
       │
  ┌────┴────┐
  │         │
PostgreSQL  Redis
  (data)   (queues)
              │
       ┌──────┼──────┬──────────────────┐
       ▼      ▼      ▼                  ▼
  ingestion  transcript  ai-summary  curriculum
   worker     worker      worker      worker
                │
           faster-whisper
            + yt-dlp
            + FFmpeg
```

All background jobs are handled by **RQ** (Redis Queue). Each worker subscribes to its own named queue. The API enqueues jobs; workers pick them up asynchronously. The frontend polls job status until completion.

---

## Repository structure

```
apps/
  api/                   ← FastAPI backend (Python 3.12)
    app/
      api/routes/        ← Route handlers (one file per resource)
      core/              ← Config, security, status constants
      db/                ← SQLAlchemy session + base
      models/            ← ORM models
      repositories/      ← DB access layer (one file per model)
      schemas/           ← Pydantic request/response schemas
      services/          ← Business logic
      workers/           ← RQ job handlers
    alembic/             ← Database migrations
    scripts/seed.py      ← Creates the demo user
  web/                   ← Next.js 15 frontend (TypeScript)
    src/
      app/(app)/         ← Authenticated routes (dashboard, spaces, settings)
      app/api/v1/        ← Server-side proxy to the FastAPI backend
      components/        ← React components
      hooks/             ← Custom React hooks
      lib/               ← Utilities (API client, helpers)
      stores/            ← Zustand global state (auth, spaces)
      middleware.ts       ← Redirects unauthenticated users to /login
packages/
  shared/                ← TypeScript types shared between web and other packages
extension/               ← Chrome/Edge Manifest V3 browser extension
scripts/dev-all.sh       ← Single-command local dev runner
docker/                  ← Postgres init SQL + Redis config
docker-compose.yml       ← Infra + app services
```

---

## How things fit together

1. **Users** authenticate via email/password or Google OAuth. The backend issues a JWT stored as a cookie by the frontend.
2. **Learning Spaces** are containers (e.g. "Machine Learning", "React Advanced"). Each space holds videos and an optional AI-reconstructed curriculum.
3. **Videos** are added by pasting a YouTube or Coursera URL. The ingestion worker fetches metadata (title, duration, author, thumbnail) without downloading any video file.
4. **Transcription** runs in background. YouTube captions are used when available (fast path); otherwise the transcript worker downloads audio-only, processes it with FFmpeg, and runs faster-whisper for speech-to-text. Segments with timestamps are stored in the DB.
5. **Curriculum reconstruction** analyses all videos in a space and builds ordered learning modules with difficulty levels, prerequisites, and rationale. Users can manually reorder items; changes persist to the DB immediately without needing a full rebuild.
6. **AI summaries** chunk the transcript and call an LLM (via OpenRouter, a local Ollama instance, or the built-in heuristic) to produce key concepts, key takeaways, a summary paragraph, and review questions.
7. **Search** indexes every video's transcript and metadata into Meilisearch for full-text search across all spaces.
8. **The browser extension** injects a "Save to Recall" button on YouTube pages for one-click ingestion.

---

## Full ingestion workflow

```
User pastes URL → POST /api/v1/spaces/{id}/ingest
                         │
             IngestionService (api)
          validates URL + detects platform
       (YouTube video / playlist / Coursera course)
          creates Source + IngestionJob rows
          enqueues job in Redis
                         │
                         │  queue: recall-ingestion
                         ▼
               ingestion_worker.py
                         │
             yt-dlp / httpx (Coursera)
                         │
           for each video found:
             upsert Video row
             update job progress counters
             enqueue TranscriptJob
                         │
                    Job → "completed"
```

- Duplicate URLs within the same space are skipped (tracked in `duplicate_count`).
- Playlists are capped by `INGESTION_MAX_PLAYLIST_ITEMS` (default 100).
- If the UI is stuck on "Reading source…", the ingestion worker is likely not running.

---

## Transcription workflow

```
Video created → TranscriptJob enqueued in recall-transcripts
                                  │
                    transcript_worker.py
                                  │
          1. Try YouTube captions (yt-dlp)
             → fast, no GPU needed
          
          2. If no captions:
             a. yt-dlp downloads audio-only (m4a/webm)
             b. FFmpeg converts to wav
             c. faster-whisper transcribes
                with VAD filter enabled
                                  │
                TranscriptSegment rows saved
                (start_time, end_time, text, order_index)
                                  │
                Job → "completed"
                Audio temp files deleted
```

Key settings:

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL_NAME` | `tiny` | Model size: `tiny` / `base` / `small` / `medium` / `large-v3` |
| `WHISPER_LANGUAGE` | _(auto-detect)_ | Force a language code (e.g. `en`, `pt`) |
| `WHISPER_FP16` | `false` | Enable FP16 — requires a CUDA GPU |
| `TRANSCRIPT_PREFER_YOUTUBE_CAPTIONS` | `true` | Use YT captions as fast path |
| `TRANSCRIPT_JOB_TIMEOUT_SECONDS` | `7200` | Max job duration |

> Use `base` or `small` for better accuracy. `large-v3` is the best quality but requires a GPU.

---

## Curriculum reconstruction

After videos are added, a curriculum reconstruction can be triggered from the space page.

```
POST /api/v1/spaces/{id}/curriculum/rebuild
              │
  CurriculumReconstructionService
              │
  Provider selection:
    heuristic (default) — no LLM, uses metadata signals
    openrouter          — calls OpenRouter API
    ollama              — calls local Ollama instance
              │
              │  queue: curriculum-reconstruction
              ▼
  curriculum_reconstruction_worker.py
              │
  1. Build video context objects
  2. Run provider → analyse_videos()
  3. Upsert VideoCurriculumProfile per video
     (difficulty, prerequisites, module hint…)
  4. Build dependency graph → topological sort
  5. Group videos into LearningModule rows
  6. Save ordered ModuleVideo rows
  7. Job → "completed"
```

**Manual reordering** works without a rebuild. The arrow buttons and position selector in the curriculum sidebar call `PATCH .../curriculum/videos/{id}/override`, which immediately updates the `module_video.order_index` rows in the DB and returns the fresh curriculum. No rebuild needed.

---

## AI summaries

Each video can have an AI-generated summary, triggered automatically after transcription or manually.

```
POST /api/v1/videos/{id}/ai-summaries
              │
  AISummaryService → enqueues job in ai-summary queue
              │
  ai_summary_worker.py
              │
  1. Load transcript segments
  2. Chunk into overlapping windows (~1800 chars)
  3. For each chunk: call LLM
     → key concepts, key takeaways, summary
  4. Merge chunks → deduplicate concepts
  5. Generate review questions
  6. Save AISummary row
  7. Job → "completed"
```

AI provider via `AI_PROVIDER`:

| Value | Description |
|---|---|
| `heuristic` | Keyword extraction, no LLM (always works, lower quality) |
| `openrouter` | OpenRouter API — requires `OPENROUTER_API_KEY` |
| `ollama` | Local Ollama instance — requires `OLLAMA_BASE_URL` |
| `auto` | Tries OpenRouter, falls back to heuristic |

---

## Search

Meilisearch indexes every video's title, description, author and transcript text.

```
GET /api/v1/search?q=...&space_id=...
         │
  SearchService → Meilisearch HTTP API
         │
  Returns ranked results with snippet highlights
```

The index is created on API startup. Videos are indexed after ingestion and re-indexed after transcription completes. Set `SEARCH_ENABLED=false` to disable.

---

## Browser extension

Located in `extension/`. Manifest V3 for Chrome and Edge.

**Installing:**
1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder

**What it does:**
- Injects a "Save to Recall" button on YouTube watch pages
- Provides a popup to log in, select a target space and manually save URLs
- Stores the auth token locally and attaches it to all Recall API calls

The extension reads `RECALL_API_URL` from its storage (defaults to `http://localhost:8000`). Point this to your deployed API URL for production use.

---

## Authentication

- **Email/password:** `POST /api/v1/auth/register` and `POST /api/v1/auth/login`
- **Google OAuth:** `POST /api/v1/auth/google` with a Google ID token (issued by Google Identity Services on the frontend)
- All protected endpoints require `Authorization: Bearer <token>`
- Tokens are JWTs signed with `JWT_SECRET_KEY`, valid for `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default 7 days)

**Demo account** (created by the seed script):
```
email:    demo@recall.dev
password: recall-demo-123
```

---

## API reference

Interactive docs at `http://localhost:8000/docs` when running locally.

**Auth**
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Email/password → JWT |
| `POST` | `/api/v1/auth/google` | Google ID token → JWT |
| `GET` | `/api/v1/auth/me` | Current user |

**Spaces**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/spaces` | List spaces |
| `POST` | `/api/v1/spaces` | Create space |
| `GET` | `/api/v1/spaces/{id}` | Get space (includes videos) |
| `PATCH` | `/api/v1/spaces/{id}` | Update space |
| `DELETE` | `/api/v1/spaces/{id}` | Delete space |

**Ingestion**
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/spaces/{id}/ingest` | Enqueue ingestion job |
| `GET` | `/api/v1/ingestion/jobs/{job_id}` | Poll job status |

**Videos**
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/spaces/{id}/videos` | Add video manually |
| `PATCH` | `/api/v1/videos/{id}` | Update video (e.g. mark completed) |
| `DELETE` | `/api/v1/videos/{id}` | Remove video |

**Transcripts**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/videos/{id}/transcript` | Get transcript segments |
| `POST` | `/api/v1/videos/{id}/transcript/jobs` | Trigger transcription |
| `GET` | `/api/v1/transcripts/jobs/{job_id}` | Poll transcript job |

**AI Summaries**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/videos/{id}/ai-summaries/latest` | Get latest summary |
| `POST` | `/api/v1/videos/{id}/ai-summaries` | Request new summary |
| `GET` | `/api/v1/ai-summaries/jobs/{job_id}` | Poll summary job |

**Curriculum**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/spaces/{id}/curriculum` | Get curriculum |
| `POST` | `/api/v1/spaces/{id}/curriculum/rebuild` | Rebuild curriculum |
| `PATCH` | `/api/v1/spaces/{id}/curriculum/videos/{video_id}/override` | Manual reorder |
| `GET` | `/api/v1/curriculum/jobs/{job_id}` | Poll curriculum job |

**Search**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/search` | Full-text search (`?q=...&space_id=...`) |

**Notes**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/videos/{id}/notes` | List notes for video |
| `POST` | `/api/v1/videos/{id}/notes` | Create note |
| `PATCH` | `/api/v1/videos/{id}/notes/{note_id}` | Update note |
| `DELETE` | `/api/v1/videos/{id}/notes/{note_id}` | Delete note |

---

## Running locally

### Prerequisites

- Node.js 20+ and pnpm 9+
- Python 3.12+
- Docker (for Postgres, Redis and Meilisearch)

### 1. Install dependencies

```bash
# JS
pnpm install

# Python (inside apps/api)
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ../..
```

### 2. Configure environment

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
```

The only value you **must** change before running is `JWT_SECRET_KEY` in `apps/api/.env`. Everything else works with defaults for local development.

Optional extras:
```bash
# Enable AI summaries
OPENROUTER_API_KEY=sk-or-...
AI_PROVIDER=openrouter

# Enable Google login
GOOGLE_OAUTH_CLIENT_IDS=<client-id>.apps.googleusercontent.com
```

### 3. Start everything

```bash
pnpm dev:all
```

This single command:
- Starts Postgres, Redis and Meilisearch via Docker
- Applies Alembic migrations
- Starts FastAPI with hot reload
- Starts all four RQ workers
- Starts the Next.js dev server
- Handles port conflicts automatically

Open http://localhost:3000 · API docs at http://localhost:8000/docs

### 4. Seed the demo account

```bash
cd apps/api
source .venv/bin/activate
python -m scripts.seed
```

Login: `demo@recall.dev` / `recall-demo-123`

### Individual services

```bash
pnpm dev:api
pnpm dev:web
pnpm dev:worker              # ingestion worker
pnpm dev:transcript-worker
pnpm dev:ai-worker
pnpm dev:curriculum-worker
```

### Checks

```bash
pnpm lint
pnpm typecheck
cd apps/api && ruff check .
```

---

## Running with Docker

```bash
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET_KEY

docker compose up --build
```

| Service | Port |
|---|---|
| web | 3000 |
| api | 8000 |
| postgres | 5433 |
| redis | 6379 |
| meilisearch | 7700 |

The `api` container applies Alembic migrations on startup.

---

## Environment variables

Copy `.env.example` → `.env` (Docker) and `apps/api/.env.example` → `apps/api/.env` (local dev).

**The real `.env` files are excluded from git by `.gitignore`. Never commit them.**

### Core

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | **Change in production.** Any random 32+ character string |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins (comma-separated) |

### Ingestion

| Variable | Default | Description |
|---|---|---|
| `INGESTION_MAX_PLAYLIST_ITEMS` | `100` | Max videos pulled from a playlist |
| `YT_DLP_SOCKET_TIMEOUT_SECONDS` | `20` | Timeout for yt-dlp network calls |

### Transcription

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL_NAME` | `tiny` | faster-whisper model size |
| `WHISPER_LANGUAGE` | _(auto)_ | Force a language (e.g. `en`, `pt`) |
| `WHISPER_FP16` | `false` | Float16 — GPU only |
| `TRANSCRIPT_PREFER_YOUTUBE_CAPTIONS` | `true` | Use YT captions as fast path |
| `TRANSCRIPT_TMP_PATH` | `/tmp/recall-transcripts` | Temp audio directory |

### AI

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `heuristic` | `heuristic` / `openrouter` / `ollama` / `auto` |
| `OPENROUTER_API_KEY` | — | Required when using OpenRouter |
| `OPENROUTER_MODEL` | `openai/gpt-oss-120b:free` | Model slug |
| `OLLAMA_BASE_URL` | — | Required when using Ollama |
| `OLLAMA_MODEL` | `mistral` | Ollama model name |

### Curriculum

| Variable | Default | Description |
|---|---|---|
| `CURRICULUM_PROVIDER` | `heuristic` | `heuristic` / `openrouter` / `ollama` |

### Search

| Variable | Default | Description |
|---|---|---|
| `SEARCH_ENABLED` | `true` | Toggle search |
| `SEARCH_URL` | `http://localhost:7700` | Meilisearch URL |
| `SEARCH_API_KEY` | — | Meilisearch master key |

### Google OAuth

| Variable | Description |
|---|---|
| `GOOGLE_OAUTH_CLIENT_IDS` | Comma-separated client IDs from Google Cloud Console |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Client ID for the frontend Google Identity button |

---

## Database migrations

Migrations live in `apps/api/alembic/versions/`.

```bash
cd apps/api

# Apply all pending migrations
alembic upgrade head

# Create a new migration (autogenerate from model changes)
alembic revision --autogenerate -m "short description"

# Roll back one step
alembic downgrade -1
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Python 3.12 |
| Database | PostgreSQL 16 |
| Queue | Redis 7 + RQ |
| Transcription | faster-whisper, yt-dlp, FFmpeg |
| Search | Meilisearch v1 |
| Auth | JWT, Google OAuth |
| Extension | Chrome/Edge Manifest V3 |
| Monorepo | pnpm workspaces |
| Containers | Docker + Compose |
