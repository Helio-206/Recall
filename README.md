# Recall

Projeto pessoal para organizar estudos a partir de videos do YouTube.

A ideia aqui e simples: criar espacos de estudo, adicionar videos ou playlists, ordenar o conteudo e acompanhar progresso. O backend cuida de auth, espacos, videos e ingestao de metadados. O frontend e so a interface para isso.

## O que tem hoje

- login e cadastro
- dashboard com espacos de estudo
- CRUD de espacos
- adicao manual de videos
- ingestao de video ou playlist do YouTube via `yt-dlp`
- transcricao com audio temporario, FFmpeg e Whisper
- workers com fila no Redis
- transcript completo em formato de documento
- progresso por espaco

Nao tem armazenamento permanente de video, resumo por IA, embeddings, busca semantica,
flashcards, quizzes, recomendacao ou pagamento.

## Stack

- web: Next.js, TypeScript, Tailwind, Zustand
- api: FastAPI, SQLAlchemy, Pydantic, JWT
- banco: PostgreSQL
- fila: Redis + RQ
- processamento: `yt-dlp`, FFmpeg e Whisper
- shared: tipos em `packages/shared`

## Estrutura

```txt
apps/
  web/
  api/
packages/
  shared/
docker/
  postgres/
  redis/
```

## Rodando local

Copiar os arquivos de ambiente:

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

Subir Postgres e Redis:

```bash
docker compose up -d postgres redis
```

Por padrao, o Recall usa a porta `5433` para o Postgres local, evitando conflito com instalacoes nativas em `5432`:

```bash
POSTGRES_PORT=5433 docker compose up -d postgres redis
```

Instalar dependencias:

```bash
pnpm install
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install -e ".[dev]"
```

Aplicar migracao e seed:

```bash
cd apps/api
alembic upgrade head
python -m scripts.seed
```

Subir web, api e workers:

```bash
pnpm dev:web
pnpm dev:api
pnpm dev:worker
pnpm dev:transcript-worker
```

Tambem da para rodar os dois workers em um unico processo local:

```bash
pnpm dev:workers
```

URLs:

- web: `http://localhost:3000`
- api: `http://localhost:8000/docs`

Login de teste:

```txt
email: demo@recall.dev
password: recall-demo-123
```

## Ingestao de metadados

A ingestao aceita URL de video ou playlist do YouTube.

Fluxo atual:

1. o frontend envia a URL
2. a API cria `Source` e `IngestionJob`
3. o worker processa a fila
4. o `yt-dlp` extrai metadados
5. os videos entram no espaco sem baixar arquivo nenhum

Se a interface ficar parada em `Reading source...`, quase sempre o worker nao esta rodando.

## Transcricao

Quando um video entra em um Learning Space, a API cria um `TranscriptJob` em background.
O worker baixa somente audio temporario, converte/processa com FFmpeg, gera segmentos com
Whisper e salva o transcript no PostgreSQL. O diretorio temporario e removido ao fim do job.

Fluxo atual:

1. o video e criado pela ingestao ou manualmente
2. a API enfileira um job em `recall-transcripts`
3. o worker tenta ler captions do YouTube primeiro
4. se nao houver captions, prepara audio temporario e usa Whisper
5. os segmentos com `start_time`, `end_time` e texto entram no banco
6. a UI mostra o status e apresenta o transcript como texto completo em parágrafos

Variaveis importantes:

```bash
TRANSCRIPT_QUEUE_NAME=recall-transcripts
TRANSCRIPT_JOB_TIMEOUT_SECONDS=7200
TRANSCRIPT_RETRY_ATTEMPTS=1
TRANSCRIPT_TMP_PATH=/tmp/recall-transcripts
TRANSCRIPT_PREFER_YOUTUBE_CAPTIONS=true
WHISPER_MODEL_NAME=tiny
WHISPER_LANGUAGE=
WHISPER_FP16=false
```

Notas:

- Captions do YouTube sao usadas como caminho rapido quando disponiveis.
- O fallback com Whisper usa FFmpeg. No Docker ele vem do sistema; no dev local o pacote `imageio-ffmpeg` fornece um binario.
- A primeira execucao do Whisper baixa o modelo configurado. Use `base` ou `small` se quiser mais qualidade.
- Para dev local em CPU, instale `torch` pelo indice CPU antes de `pip install -e ".[dev]"`.
- Nenhum arquivo de video e armazenado permanentemente.
- Se aparecer `Transcript worker looks offline`, inicie `pnpm dev:transcript-worker`.
- Se um job ficar parado, confira `rq:queue:recall-transcripts`; sem `transcript-worker`, ele fica `pending`.

## Endpoints principais

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/spaces`
- `POST /api/v1/spaces`
- `GET /api/v1/spaces/{space_id}`
- `PATCH /api/v1/spaces/{space_id}`
- `DELETE /api/v1/spaces/{space_id}`
- `POST /api/v1/spaces/{space_id}/ingest`
- `GET /api/v1/spaces/{space_id}/sources`
- `GET /api/v1/spaces/{space_id}/videos`
- `GET /api/v1/ingestion/jobs/{job_id}`
- `POST /api/v1/spaces/{space_id}/videos`
- `PATCH /api/v1/videos/{video_id}`
- `DELETE /api/v1/videos/{video_id}`
- `GET /api/v1/videos/{video_id}/transcript`
- `POST /api/v1/videos/{video_id}/transcript/jobs`
- `GET /api/v1/transcripts/jobs/{job_id}`
- `GET /api/v1/health`

## Checks rapidos

```bash
pnpm lint
pnpm typecheck
python3 -m compileall apps/api/app apps/api/scripts apps/api/alembic
```
