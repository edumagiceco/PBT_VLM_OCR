"""add notification and log settings fields

Revision ID: 20260103_000006
Revises: 20260103_000005
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 로그 설정 필드 추가
    op.add_column('settings', sa.Column('log_level', sa.String(20), nullable=False, server_default='info'))
    op.add_column('settings', sa.Column('log_retention_days', sa.Integer(), nullable=False, server_default='30'))

    # 알림 설정 필드 추가
    op.add_column('settings', sa.Column('notification_enabled', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('settings', sa.Column('notification_email', sa.String(500), nullable=False, server_default=''))
    op.add_column('settings', sa.Column('notification_webhook_url', sa.String(1000), nullable=False, server_default=''))
    op.add_column('settings', sa.Column('notification_on_ocr_complete', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('settings', sa.Column('notification_on_ocr_error', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('settings', sa.Column('notification_on_storage_warning', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('settings', sa.Column('notification_storage_threshold', sa.Integer(), nullable=False, server_default='80'))


def downgrade() -> None:
    # 알림 설정 필드 삭제
    op.drop_column('settings', 'notification_storage_threshold')
    op.drop_column('settings', 'notification_on_storage_warning')
    op.drop_column('settings', 'notification_on_ocr_error')
    op.drop_column('settings', 'notification_on_ocr_complete')
    op.drop_column('settings', 'notification_webhook_url')
    op.drop_column('settings', 'notification_email')
    op.drop_column('settings', 'notification_enabled')

    # 로그 설정 필드 삭제
    op.drop_column('settings', 'log_retention_days')
    op.drop_column('settings', 'log_level')
