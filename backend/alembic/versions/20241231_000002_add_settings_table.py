"""Add settings table for timezone and VLM configuration

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # settings 테이블 생성
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), primary_key=True, default=1),

        # 타임존 설정
        sa.Column('timezone', sa.String(100), nullable=False, server_default='Asia/Seoul'),

        # VLM 설정
        sa.Column('vlm_endpoint_url', sa.String(1000), nullable=False, server_default=''),
        sa.Column('vlm_model_name', sa.String(200), nullable=False, server_default=''),
        sa.Column('vlm_temperature', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('vlm_max_tokens', sa.Integer(), nullable=False, server_default='4096'),
        sa.Column('vlm_top_p', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('vlm_timeout', sa.Integer(), nullable=False, server_default='120'),
        sa.Column('vlm_extra_params', postgresql.JSONB(), nullable=True, server_default='{}'),

        # 메타데이터
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 기본 설정 레코드 삽입 (싱글톤)
    op.execute("""
        INSERT INTO settings (id, timezone, vlm_endpoint_url, vlm_model_name,
                             vlm_temperature, vlm_max_tokens, vlm_top_p, vlm_timeout,
                             vlm_extra_params, created_at, updated_at)
        VALUES (1, 'Asia/Seoul', '', '', 0.0, 4096, 1.0, 120, '{}', NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_table('settings')
