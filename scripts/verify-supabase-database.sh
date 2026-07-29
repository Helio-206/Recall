#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL must point to the Supabase Session pooler."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" - <<'PY'
import os

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)

with engine.connect() as connection:
    database, version = connection.execute(
        text("SELECT current_database(), version()")
    ).one()
    head = connection.execute(text("SELECT version_num FROM public.alembic_version")).scalar_one()
    table_count = connection.execute(
        text(
            "SELECT count(*) FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
        )
    ).scalar_one()
    rls_count = connection.execute(
        text(
            "SELECT count(*) FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'alembic_version' AND rowsecurity"
        )
    ).scalar_one()

print(f"database={database}")
print(f"postgres_version={version}")
print(f"alembic_head={head}")
print(f"recall_table_count={table_count}")
print(f"rls_enabled_table_count={rls_count}")
PY
