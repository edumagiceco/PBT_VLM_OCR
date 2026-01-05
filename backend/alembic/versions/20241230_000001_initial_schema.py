"""Initial schema - documents, pages, blocks

Revision ID: 0001
Revises:
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum 타입 생성 (SQLAlchemy uses enum names by default)
    op.execute("CREATE TYPE ocrmode AS ENUM ('GENERAL', 'PRECISION', 'AUTO')")
    op.execute("CREATE TYPE documentstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REVIEW')")
    op.execute("CREATE TYPE importance AS ENUM ('LOW', 'MEDIUM', 'HIGH')")
    op.execute("CREATE TYPE blocktype AS ENUM ('TEXT', 'TABLE', 'IMAGE', 'HEADER', 'FOOTER', 'LIST')")

    # documents 테이블
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('page_count', sa.Integer(), default=0),

        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('doc_type', sa.String(100), nullable=True),
        sa.Column('importance', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='importance', create_type=False), default='MEDIUM'),

        sa.Column('ocr_mode', postgresql.ENUM('GENERAL', 'PRECISION', 'AUTO', name='ocrmode', create_type=False), default='AUTO'),
        sa.Column('recommended_ocr_mode', postgresql.ENUM('GENERAL', 'PRECISION', 'AUTO', name='ocrmode', create_type=False), nullable=True),
        sa.Column('precision_score', sa.Integer(), nullable=True),

        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REVIEW', name='documentstatus', create_type=False), default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_department', 'documents', ['department'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])

    # document_pages 테이블
    op.create_table(
        'document_pages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_no', sa.Integer(), nullable=False),

        sa.Column('image_path', sa.String(1000), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),

        sa.Column('ocr_json', postgresql.JSONB(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('layout_score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),

        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_document_pages_id', 'document_pages', ['id'])
    op.create_index('ix_document_pages_document_id', 'document_pages', ['document_id'])
    op.create_index('ix_document_pages_page_no', 'document_pages', ['document_id', 'page_no'])

    # document_blocks 테이블
    op.create_table(
        'document_blocks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page_id', sa.Integer(), sa.ForeignKey('document_pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('block_order', sa.Integer(), default=0),

        sa.Column('block_type', postgresql.ENUM('TEXT', 'TABLE', 'IMAGE', 'HEADER', 'FOOTER', 'LIST', name='blocktype', create_type=False), default='TEXT'),
        sa.Column('bbox', postgresql.JSON(), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('table_json', postgresql.JSONB(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),

        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_document_blocks_id', 'document_blocks', ['id'])
    op.create_index('ix_document_blocks_page_id', 'document_blocks', ['page_id'])

    # Full-text search 인덱스 (PostgreSQL)
    op.execute("""
        CREATE INDEX ix_documents_title_trgm ON documents
        USING gin (title gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX ix_document_pages_raw_text_trgm ON document_pages
        USING gin (raw_text gin_trgm_ops)
    """)


def downgrade() -> None:
    # 인덱스 삭제
    op.execute("DROP INDEX IF EXISTS ix_document_pages_raw_text_trgm")
    op.execute("DROP INDEX IF EXISTS ix_documents_title_trgm")

    # 테이블 삭제
    op.drop_table('document_blocks')
    op.drop_table('document_pages')
    op.drop_table('documents')

    # Enum 타입 삭제
    op.execute("DROP TYPE IF EXISTS blocktype")
    op.execute("DROP TYPE IF EXISTS importance")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS ocrmode")
