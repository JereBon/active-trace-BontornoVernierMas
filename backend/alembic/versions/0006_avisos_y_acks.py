"""Create avisos and aviso_acks tables (C-15: avisos-y-acknowledgment).

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-04

Tables created:
  - avisos     : institutional notices per tenant with scope and visibility window
  - aviso_acks : per-user acknowledgment records (UNIQUE aviso_id + usuario_id)

Design:
  - scope stored as VARCHAR (not PG ENUM) so future values (MATERIA, COHORTE)
    can be added without DDL ENUM ALTER.
  - aviso_acks.aviso_id has ON DELETE CASCADE so purging an Aviso (if ever
    physical deletion is added) cleans up its ACKs automatically.
  - UNIQUE constraint on (aviso_id, usuario_id) enforces idempotent ACK at DB level.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create avisos and aviso_acks tables."""

    # ── avisos ────────────────────────────────────────────────────────────────
    op.create_table(
        "avisos",
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
            index=True,
        ),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("cuerpo", sa.String(), nullable=False),
        sa.Column(
            "scope",
            sa.String(),
            nullable=False,
            server_default="TODOS",
            comment="TODOS | ROL | USUARIO",
        ),
        sa.Column("scope_valor", sa.String(), nullable=True),
        sa.Column("vig_desde", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vig_hasta", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="False = soft-deleted",
        ),
        sa.Column(
            "publicado_por",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="user_id of the publisher (from JWT)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── aviso_acks ────────────────────────────────────────────────────────────
    op.create_table(
        "aviso_acks",
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
            index=True,
        ),
        sa.Column(
            "aviso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("avisos.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "leido_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "aviso_id",
            "usuario_id",
            name="uq_aviso_ack_aviso_usuario",
        ),
    )


def downgrade() -> None:
    """Drop aviso_acks then avisos (respect FK order)."""
    op.drop_table("aviso_acks")
    op.drop_table("avisos")
