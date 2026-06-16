"""Create mensajes_internos table (C-20: perfil-y-mensajeria-interna).

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-06

Changes:
  - Creates table 'mensajes_internos': internal messaging between users of the
    same tenant. Includes tenant_id (row-level isolation), remitente_id,
    destinatario_id, asunto, cuerpo, leido flag, hilo_id (thread linking),
    soft delete via deleted_at, and standard audit timestamps.
  - Indexes on tenant_id, remitente_id, destinatario_id, hilo_id for efficient
    inbox/sent/thread queries.

Note: No permission seeding needed — inbox is available to all authenticated
users (no special permission required per C-20 scope).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: Union[str, tuple[str, ...], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── Create mensajes_internos table (idempotent) ───────────────────────────
    table_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='mensajes_internos'"
        )
    ).fetchone()

    if not table_exists:
        op.create_table(
            "mensajes_internos",
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
                comment="FK → tenants.id — row-level tenant isolation.",
            ),
            sa.Column(
                "remitente_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — sender (sourced from JWT).",
            ),
            sa.Column(
                "destinatario_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — recipient.",
            ),
            sa.Column(
                "asunto",
                sa.String(255),
                nullable=False,
                comment="Message subject line.",
            ),
            sa.Column(
                "cuerpo",
                sa.Text,
                nullable=False,
                comment="Message body (plaintext).",
            ),
            sa.Column(
                "leido",
                sa.Boolean,
                nullable=False,
                server_default="false",
                comment="True once the recipient has viewed the message.",
            ),
            sa.Column(
                "hilo_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
                comment="Thread root message id. NULL for root messages; set for replies.",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
                comment="Timestamp of message creation.",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
                comment="Last update timestamp.",
            ),
            sa.Column(
                "deleted_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Soft delete timestamp. NULL = active.",
            ),
        )

        # ── Indexes ───────────────────────────────────────────────────────────
        op.create_index(
            "ix_mensajes_internos_tenant_id",
            "mensajes_internos",
            ["tenant_id"],
        )
        op.create_index(
            "ix_mensajes_internos_remitente_id",
            "mensajes_internos",
            ["remitente_id"],
        )
        op.create_index(
            "ix_mensajes_internos_destinatario_id",
            "mensajes_internos",
            ["destinatario_id"],
        )
        op.create_index(
            "ix_mensajes_internos_hilo_id",
            "mensajes_internos",
            ["hilo_id"],
        )


def downgrade() -> None:
    op.drop_index("ix_mensajes_internos_hilo_id", table_name="mensajes_internos")
    op.drop_index("ix_mensajes_internos_destinatario_id", table_name="mensajes_internos")
    op.drop_index("ix_mensajes_internos_remitente_id", table_name="mensajes_internos")
    op.drop_index("ix_mensajes_internos_tenant_id", table_name="mensajes_internos")
    op.drop_table("mensajes_internos")
