"""chat_identity nullable user

Revision ID: b10687498e54
Revises: a0192808753d
Create Date: 2026-02-20 12:46:12.854442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b10687498e54'
down_revision: Union[str, Sequence[str], None] = 'a0192808753d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
