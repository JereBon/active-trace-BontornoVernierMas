"""Create tenants table (C-02 foundation).

Revision ID: 0001
Revises:
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the tenants table — the root of multi-tenant data isolation."""
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.VARCHAR(length=255),
            nullable=False,
        ),
        sa.Column(
            "nombre",
            sa.VARCHAR(length=255),
            nullable=False,
        ),
        sa.Column(
            "activo",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    # Unique index enforces the slug uniqueness constraint
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)


def downgrade() -> None:
    """Drop the tenants table."""
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
