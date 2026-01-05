"""add_ocr_settings_fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-03 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # settings 테이블에 OCR 관련 컬럼 추가
    op.add_column('settings', sa.Column('ocr_default_mode', sa.String(20), nullable=False, server_default='auto'))
    op.add_column('settings', sa.Column('ocr_precision_threshold', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('settings', sa.Column('ocr_high_res_dpi', sa.Integer(), nullable=False, server_default='300'))
    op.add_column('settings', sa.Column('ocr_language', sa.String(50), nullable=False, server_default='kor+eng'))
    op.add_column('settings', sa.Column('ocr_preserve_layout', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    # OCR 관련 컬럼 삭제
    op.drop_column('settings', 'ocr_preserve_layout')
    op.drop_column('settings', 'ocr_language')
    op.drop_column('settings', 'ocr_high_res_dpi')
    op.drop_column('settings', 'ocr_precision_threshold')
    op.drop_column('settings', 'ocr_default_mode')
