"""Create audit_logs table (C-05: audit-log).

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-04

Creates:
  - audit_logs : immutable append-only audit log for all significant actions.

The table intentionally has NO updated_at or deleted_at columns.
Audit log entries are immutable: they are never modified or soft-deleted.

Indices:
  - ix_audit_logs_tenant_id_fecha_hora  : composite index for tenant-scoped
    chronological queries (most common access pattern).
  - ix_audit_logs_actor_id              : index for per-actor queries.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "actor_impersonado_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "accion",
            sa.String(128),
            nullable=False,
        ),
        sa.Column(
            "detalle",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "filas_afectadas",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "ip",
            sa.String(64),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "user_agent",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )

    # Composite index: most queries filter by tenant + time range
    op.create_index(
        "ix_audit_logs_tenant_id_fecha_hora",
        "audit_logs",
        ["tenant_id", "fecha_hora"],
    )

    # Index for actor-specific queries (e.g. "show me what user X did")
    op.create_index(
        "ix_audit_logs_actor_id",
        "audit_logs",
        ["actor_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id_fecha_hora", table_name="audit_logs")
    op.drop_table("audit_logs")
