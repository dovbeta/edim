"""chat_identity nullable user

Revision ID: 0e7390b8336b
Revises: b10687498e54
Create Date: 2026-02-20 12:56:46.863697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e7390b8336b'
down_revision: Union[str, Sequence[str], None] = 'b10687498e54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "chat_identities",
        "user_id",
        existing_type=sa.UUID(),
        nullable=True
    )

def downgrade():
    op.alter_column(
        "chat_identities",
        "user_id",
        existing_type=sa.UUID(),
        nullable=False
    )
