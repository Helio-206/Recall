# Recall

Projeto pessoal para organizar estudos a partir de videos do YouTube.

A ideia aqui e simples: criar espacos de estudo, adicionar videos ou playlists, ordenar o conteudo e acompanhar progresso. O backend cuida de auth, espacos, videos e ingestao de metadados. O frontend e so a interface para isso.

## O que tem hoje

- login e cadastro
- dashboard com espacos de estudo
- CRUD de espacos
- adicao manual de videos
- ingestao de video ou playlist do YouTube via `yt-dlp`
- worker com fila no Redis
- progresso por espaco

Nao tem download de video, transcricao, IA, embeddings ou pagamento.

## Stack

- web: Next.js, TypeScript, Tailwind, Zustand
- api: FastAPI, SQLAlchemy, Pydantic, JWT
- banco: PostgreSQL
- fila: Redis + RQ
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

Se a porta `5432` ja estiver ocupada na maquina, usa `5433` no `apps/api/.env` e sobe assim:

```bash
POSTGRES_PORT=5433 docker compose up -d postgres redis
```

Instalar dependencias:

```bash
pnpm install
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Aplicar migracao e seed:

```bash
cd apps/api
alembic upgrade head
python -m scripts.seed
```

Subir web, api e worker:

```bash
pnpm dev:web
pnpm dev:api
pnpm dev:worker
```

URLs:

- web: `http://localhost:3000`
- api: `http://localhost:8000/docs`

Login de teste:

```txt
email: demo@recall.dev
password: recall-demo-123
```

## Ingestao

A ingestao aceita URL de video ou playlist do YouTube.

Fluxo atual:

1. o frontend envia a URL
2. a API cria `Source` e `IngestionJob`
3. o worker processa a fila
4. o `yt-dlp` extrai metadados
5. os videos entram no espaco sem baixar arquivo nenhum

Se a interface ficar parada em `Reading source...`, quase sempre o worker nao esta rodando.

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
- `GET /api/v1/health`

## Checks rapidos

```bash
pnpm lint
pnpm typecheck
python3 -m compileall apps/api/app apps/api/scripts
```
