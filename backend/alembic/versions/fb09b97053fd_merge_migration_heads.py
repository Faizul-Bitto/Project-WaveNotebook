"""merge migration heads

Revision ID: fb09b97053fd
Revises: 2026_add_bogo_variant, 2026_add_page_title
Create Date: 2026-08-22 22:25:07.218832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb09b97053fd'
down_revision: Union[str, Sequence[str], None] = ('2026_add_bogo_variant', '2026_add_page_title')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
