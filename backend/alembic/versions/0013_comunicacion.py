"""Create comunicaciones table and add comunicacion_requiere_aprobacion to tenants (C-12).

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-05

Changes:
  - Adds column 'comunicacion_requiere_aprobacion' (BOOLEAN NOT NULL DEFAULT TRUE)
    to table 'tenants'. Controls whether bulk sends require approval before dispatch.
  - Creates table 'comunicaciones': E21 from KB §04. Stores outbound email
    communications with AES-256 encrypted destinatario, lote_id for batch grouping,
    state machine (Pendiente→Enviando→Enviado|Error, Pendiente→Cancelado), and
    soft delete.
  - Seeds permissions: comunicacion:enviar, comunicacion:aprobar.
  - Indexes on (tenant_id), (lote_id), (estado), (tenant_id, lote_id).
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: Union[str, tuple[str, ...], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Add column to tenants (idempotent) ──────────────────────────────────
    # Use raw SQL with IF NOT EXISTS to tolerate test DBs where create_all
    # already ran the Communicacion model (which doesn't add this column).
    conn = op.get_bind()
    col_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='tenants' AND column_name='comunicacion_requiere_aprobacion'"
        )
    ).fetchone()
    if not col_exists:
        op.add_column(
            "tenants",
            sa.Column(
                "comunicacion_requiere_aprobacion",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("TRUE"),
                comment=(
                    "When True, bulk sends (>1 recipient) require explicit approval "
                    "from a user with comunicacion:aprobar before the worker dispatches them."
                ),
            ),
        )

    # ── 2. Create comunicaciones table (idempotent) ────────────────────────────
    table_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name='comunicaciones'"
        )
    ).fetchone()
    if table_exists:
        return  # table already exists (created by create_all in tests)

    op.create_table(
        "comunicaciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="Internal UUID primary key.",
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK → tenants.id — enforces row-level tenant isolation.",
        ),
        sa.Column(
            "enviado_por",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK → usuarios.id — the user who triggered the send.",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK → materias.id — the materia context for this communication (nullable for system-wide sends).",
        ),
        sa.Column(
            "destinatario",
            sa.Text(),
            nullable=False,
            comment="AES-256-GCM encrypted email address of the recipient (PII at rest).",
        ),
        sa.Column(
            "asunto",
            sa.Text(),
            nullable=False,
            comment="Email subject line (plaintext, no PII).",
        ),
        sa.Column(
            "cuerpo",
            sa.Text(),
            nullable=False,
            comment="Email body with variables already substituted (plaintext, no PII).",
        ),
        sa.Column(
            "estado",
            sa.String(length=20),
            nullable=False,
            server_default="Pendiente",
            comment="State machine: Pendiente | Enviando | Enviado | Error | Cancelado.",
        ),
        sa.Column(
            "aprobado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
            comment=(
                "True when a user with comunicacion:aprobar has approved this message "
                "for dispatch. The worker only processes aprobado=True messages."
            ),
        ),
        sa.Column(
            "lote_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Groups all messages from the same bulk send operation.",
        ),
        sa.Column(
            "enviado_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when the message was successfully dispatched. NULL until Enviado.",
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
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp. NULL = active; non-NULL = deleted.",
        ),
    )

    # ── 3. Indexes ─────────────────────────────────────────────────────────────
    op.create_index("ix_comunicaciones_tenant_id", "comunicaciones", ["tenant_id"])
    op.create_index("ix_comunicaciones_lote_id", "comunicaciones", ["lote_id"])
    op.create_index("ix_comunicaciones_estado", "comunicaciones", ["estado"])
    op.create_index(
        "ix_comunicaciones_tenant_lote",
        "comunicaciones",
        ["tenant_id", "lote_id"],
    )

    # Note: comunicacion:enviar and comunicacion:aprobar permissions are already
    # seeded by migration 0003 (RBAC). No additional seeding required here.


def downgrade() -> None:
    conn = op.get_bind()

    # Note: comunicacion:enviar and comunicacion:aprobar were seeded by migration 0003.
    # We do NOT delete them here — they belong to the RBAC foundation, not this migration.

    # Drop indexes (only if they exist — they may not exist if upgrade was early-exited)
    for idx in [
        "ix_comunicaciones_tenant_lote",
        "ix_comunicaciones_estado",
        "ix_comunicaciones_lote_id",
        "ix_comunicaciones_tenant_id",
    ]:
        idx_exists = conn.execute(
            sa.text(
                "SELECT 1 FROM pg_indexes WHERE indexname = :name"
            ),
            {"name": idx},
        ).fetchone()
        if idx_exists:
            op.drop_index(idx, table_name="comunicaciones")

    # Drop table if it was created by the migration (not by create_all)
    # We drop it unconditionally — if it exists
    table_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='comunicaciones'"
        )
    ).fetchone()
    if table_exists:
        op.drop_table("comunicaciones")

    # Remove column from tenants (only if it exists)
    col_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='tenants' AND column_name='comunicacion_requiere_aprobacion'"
        )
    ).fetchone()
    if col_exists:
        op.drop_column("tenants", "comunicacion_requiere_aprobacion")
