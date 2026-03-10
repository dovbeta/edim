"""add indexes

Revision ID: 1387bfa5d048
Revises: 37df477dd94a
Create Date: 2026-03-10 19:25:21.132389
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1387bfa5d048'
down_revision: Union[str, Sequence[str], None] = '37df477dd94a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # units
    op.create_index(
        "idx_units_number",
        "units",
        ["number"],
        unique=False
    )

    op.create_index(
        "idx_units_building_id",
        "units",
        ["building_id"],
        unique=False
    )

    # user_units
    op.create_index(
        "idx_user_units_user_id",
        "user_units",
        ["user_id"],
        unique=False
    )

    op.create_index(
        "idx_user_units_unit_id",
        "user_units",
        ["unit_id"],
        unique=False
    )

    op.create_index(
        "idx_user_units_user_unit",
        "user_units",
        ["user_id", "unit_id"],
        unique=False
    )

    # vehicles
    op.create_index(
        "idx_vehicles_user_id",
        "vehicles",
        ["user_id"],
        unique=False
    )

    op.create_index(
        "idx_vehicles_license_plate",
        "vehicles",
        ["license_plate"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("idx_units_number", table_name="units")
    op.drop_index("idx_units_building_id", table_name="units")

    op.drop_index("idx_user_units_user_id", table_name="user_units")
    op.drop_index("idx_user_units_unit_id", table_name="user_units")
    op.drop_index("idx_user_units_user_unit", table_name="user_units")

    op.drop_index("idx_vehicles_user_id", table_name="vehicles")
    op.drop_index("idx_vehicles_license_plate", table_name="vehicles")