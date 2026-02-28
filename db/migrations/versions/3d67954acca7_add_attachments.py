"""add_attachments

Revision ID: 3d67954acca7
Revises: 0002_add_image_url_to_topic
Create Date: 2026-02-28 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d67954acca7'
down_revision = '0002_add_image_url_to_topic'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=16), nullable=False, comment="'topic' or 'question'"),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('attachment_type', sa.String(length=16), nullable=False, comment="'photo' or 'document'"),
        sa.Column('file_key', sa.String(length=512), nullable=False),
        sa.Column('file_name', sa.String(length=256), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'idx_entity_type_id',
        'attachments',
        ['entity_type', 'entity_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_entity_type_id', table_name='attachments')
    op.drop_table('attachments')
