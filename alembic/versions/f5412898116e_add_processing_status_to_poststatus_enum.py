"""add PROCESSING status to poststatus enum

Revision ID: f5412898116e
Revises: e3221797005d
Create Date: 2026-07-28 22:31:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f5412898116e'
down_revision: Union[str, Sequence[str], None] = 'e3221797005d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE poststatus ADD VALUE IF NOT EXISTS 'PROCESSING'")


def downgrade() -> None:
    pass
