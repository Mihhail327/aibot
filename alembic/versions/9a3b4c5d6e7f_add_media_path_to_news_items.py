"""Add media_path to news_items

Revision ID: 9a3b4c5d6e7f
Revises: 8f2e10484b90
Create Date: 2026-07-26 20:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a3b4c5d6e7f'
down_revision: Union[str, Sequence[str], None] = '8f2e10484b90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('news_items', sa.Column('media_path', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('news_items', 'media_path')
