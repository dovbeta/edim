"""add external_id to building and unit

Revision ID: cf84e378be7e
Revises: b4519dd6397f
Create Date: 2026-02-21 14:16:28.151951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf84e378be7e'
down_revision: Union[str, Sequence[str], None] = 'b4519dd6397f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('buildings', sa.Column('external_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_buildings_external_id'), 'buildings', ['external_id'], unique=False)
    op.add_column('units', sa.Column('external_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_units_external_id'), 'units', ['external_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_units_external_id'), table_name='units')
    op.drop_column('units', 'external_id')
    op.drop_index(op.f('ix_buildings_external_id'), table_name='buildings')
    op.drop_column('buildings', 'external_id')
