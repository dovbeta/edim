"""extended unit_residents view

Revision ID: 07e893d1bbc6
Revises: 1387bfa5d048
Create Date: 2026-03-11 07:11:33.968436
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '07e893d1bbc6'
down_revision: Union[str, Sequence[str], None] = '1387bfa5d048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        DROP VIEW IF EXISTS unit_residents
    """)

    op.execute("""
        CREATE VIEW unit_residents AS
        SELECT
            u.id AS unit_id,
            u.number AS unit_number,
            u.unit_type,

            b.id AS building_id,
            b.address AS building_address,
            o.id AS organization_id,

            usr.id AS user_id,
            usr.first_name,
            usr.last_name,
            usr.phone,

            uu.role AS resident_role

        FROM units u
        JOIN buildings b ON b.id = u.building_id
        JOIN organizations o ON o.id = b.organization_id
        JOIN user_units uu ON uu.unit_id = u.id
        JOIN users usr ON usr.id = uu.user_id
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DROP VIEW IF EXISTS unit_residents")

    op.execute("""
        CREATE VIEW unit_residents AS
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