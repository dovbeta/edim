"""add units_extended view

Revision ID: c96d3e794eea
Revises: 588465b7ab7d
Create Date: 2026-03-10 19:03:16.784852
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c96d3e794eea'
down_revision: Union[str, Sequence[str], None] = '588465b7ab7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        CREATE OR REPLACE VIEW units_extended AS
        SELECT
            u.id AS unit_id,
            u.number AS unit_number,
            u.personal_account,
            u.unit_type,
            u.floor,
            u.section,
            u.rooms,
            u.area_total,
            u.debt_total,

            b.id AS building_id,
            b.address AS building_address,

            o.id AS organization_id,
            o.name AS organization_name

        FROM units u
        JOIN buildings b ON b.id = u.building_id
        JOIN organizations o ON o.id = b.organization_id
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        DROP VIEW IF EXISTS units_extended
    """)