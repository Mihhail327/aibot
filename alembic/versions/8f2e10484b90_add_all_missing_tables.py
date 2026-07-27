"""Add missing tables (admin_settings, keywords, news_items, posts)

Revision ID: 8f2e10484b90
Revises: 7d8f50276cf6
Create Date: 2026-07-26 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8f2e10484b90'
down_revision: Union[str, Sequence[str], None] = '7d8f50276cf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: admin_settings
    op.create_table(
        'admin_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Table: keywords
    op.create_table(
        'keywords',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keywords_word'), 'keywords', ['word'], unique=True)

    # 3. Table: news_items
    op.create_table(
        'news_items',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_items_url'), 'news_items', ['url'], unique=True)
    op.create_index(op.f('ix_news_items_source'), 'news_items', ['source'], unique=False)

    # 4. Table: posts
    post_status_enum = sa.Enum('NEW', 'GENERATED', 'PUBLISHED', 'FAILED', name='poststatus')
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('news_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_text', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', post_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['news_id'], ['news_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posts_news_id'), 'posts', ['news_id'], unique=False)
    op.create_index(op.f('ix_posts_status'), 'posts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_posts_status'), table_name='posts')
    op.drop_index(op.f('ix_posts_news_id'), table_name='posts')
    op.drop_table('posts')
    sa.Enum(name='poststatus').drop(op.get_bind(), checkfirst=False)

    op.drop_index(op.f('ix_news_items_source'), table_name='news_items')
    op.drop_index(op.f('ix_news_items_url'), table_name='news_items')
    op.drop_table('news_items')

    op.drop_index(op.f('ix_keywords_word'), table_name='keywords')
    op.drop_table('keywords')

    op.drop_table('admin_settings')
