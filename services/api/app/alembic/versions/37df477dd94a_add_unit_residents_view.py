"""add unit_residents view

Revision ID: 37df477dd94a
Revises: c96d3e794eea
Create Date: 2026-03-10 19:08:12.012908
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37df477dd94a'
down_revision: Union[str, Sequence[str], None] = 'c96d3e794eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        CREATE OR REPLACE VIEW unit_residents AS
        SELECT
            u.id AS unit_id,
            u.number AS unit_number,

            usr.id AS user_id,
            usr.first_name,
            usr.last_name,
            usr.phone,

            uu.role AS resident_role

        FROM units u
        JOIN user_units uu ON uu.unit_id = u.id
        JOIN users usr ON usr.id = uu.user_id
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        DROP VIEW IF EXISTS unit_residents
    """)