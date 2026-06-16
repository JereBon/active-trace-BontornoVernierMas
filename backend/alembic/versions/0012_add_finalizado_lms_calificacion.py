"""Add finalizado_lms column to calificacion table (C-11).

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-05

Changes:
  - Adds column 'finalizado_lms' (BOOLEAN NOT NULL DEFAULT FALSE) to
    table 'calificacion'. This field tracks whether the LMS reported the
    student has finalised the activity but it has not been graded yet
    (used for F2.6 / RN-07 / RN-08: export sin corregir).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
# Merges the two parallel heads from C-10 (0010) and C-11/C-13 (0011)
revision: str = "0012"
down_revision: Union[str, tuple[str, ...], None] = ("0010", "0011")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "calificacion",
        sa.Column(
            "finalizado_lms",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="True when the LMS reports the student finalised the activity but no grade is present yet (RN-07).",
        ),
    )


def downgrade() -> None:
    op.drop_column("calificacion", "finalizado_lms")
