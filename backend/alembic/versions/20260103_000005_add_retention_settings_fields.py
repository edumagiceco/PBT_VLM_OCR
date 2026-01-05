"""add retention settings fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-03
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 문서 보관 정책 설정 필드 추가
    op.add_column('settings', sa.Column('retention_enabled', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('settings', sa.Column('retention_days', sa.Integer(), nullable=False, server_default='90'))
    op.add_column('settings', sa.Column('retention_min_documents', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('settings', sa.Column('retention_delete_files', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('settings', sa.Column('retention_auto_run_hour', sa.Integer(), nullable=False, server_default='3'))


def downgrade() -> None:
    op.drop_column('settings', 'retention_auto_run_hour')
    op.drop_column('settings', 'retention_delete_files')
    op.drop_column('settings', 'retention_min_documents')
    op.drop_column('settings', 'retention_days')
    op.drop_column('settings', 'retention_enabled')
