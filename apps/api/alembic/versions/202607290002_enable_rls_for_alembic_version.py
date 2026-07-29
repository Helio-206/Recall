"""enable row level security for alembic version

Revision ID: 202607290002
Revises: 202607290001
Create Date: 2026-07-29 14:45:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202607290002"
down_revision: str | None = "202607290001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")
