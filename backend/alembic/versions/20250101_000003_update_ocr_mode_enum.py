"""Update OCRMode enum: general->fast, add accurate

Revision ID: 20250101_000003
Revises: 20241231_000002
Create Date: 2025-01-01

OCR 모드 변경:
- general -> fast (Tesseract 기반)
- 신규: accurate (PaddleOCR 딥러닝 기반)
- precision 유지 (Chandra VLM 기반)
- auto 유지 (자동 선택)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL에서 enum 값 변경
    # 현재 enum: GENERAL, PRECISION, AUTO (대문자)
    # 새로운 enum: fast, accurate, precision, auto (소문자)

    # 1. 새로운 값 추가 (소문자)
    op.execute("ALTER TYPE ocrmode ADD VALUE IF NOT EXISTS 'fast'")
    op.execute("ALTER TYPE ocrmode ADD VALUE IF NOT EXISTS 'accurate'")
    op.execute("ALTER TYPE ocrmode ADD VALUE IF NOT EXISTS 'precision'")
    op.execute("ALTER TYPE ocrmode ADD VALUE IF NOT EXISTS 'auto'")

    # 2. 기존 대문자 값을 소문자로 변환
    op.execute("""
        UPDATE documents
        SET ocr_mode = 'fast'
        WHERE ocr_mode::text = 'GENERAL'
    """)
    op.execute("""
        UPDATE documents
        SET ocr_mode = 'precision'
        WHERE ocr_mode::text = 'PRECISION'
    """)
    op.execute("""
        UPDATE documents
        SET ocr_mode = 'auto'
        WHERE ocr_mode::text = 'AUTO'
    """)
    op.execute("""
        UPDATE documents
        SET recommended_ocr_mode = 'fast'
        WHERE recommended_ocr_mode::text = 'GENERAL'
    """)
    op.execute("""
        UPDATE documents
        SET recommended_ocr_mode = 'precision'
        WHERE recommended_ocr_mode::text = 'PRECISION'
    """)
    op.execute("""
        UPDATE documents
        SET recommended_ocr_mode = 'auto'
        WHERE recommended_ocr_mode::text = 'AUTO'
    """)


def downgrade() -> None:
    # 다운그레이드: fast -> general로 복원
    op.execute("""
        UPDATE documents
        SET ocr_mode = 'general'
        WHERE ocr_mode = 'fast'
    """)
    op.execute("""
        UPDATE documents
        SET recommended_ocr_mode = 'general'
        WHERE recommended_ocr_mode = 'fast'
    """)
    op.execute("""
        UPDATE documents
        SET ocr_mode = 'general'
        WHERE ocr_mode = 'accurate'
    """)
    op.execute("""
        UPDATE documents
        SET recommended_ocr_mode = 'general'
        WHERE recommended_ocr_mode = 'accurate'
    """)
