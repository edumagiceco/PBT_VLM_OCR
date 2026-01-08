"""
Pytest configuration and shared fixtures
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import Base
from app.models.document import (
    Document, DocumentPage, DocumentBlock,
    OCRMode, DocumentStatus, Importance, BlockType
)


# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture
def in_memory_db() -> Generator[Session, None, None]:
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


# ============================================================
# Document Fixtures
# ============================================================

@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing"""
    return Document(
        id=1,
        title="Test Document",
        original_filename="test.pdf",
        file_path="documents/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        page_count=10,
        department="Engineering",
        doc_type="report",
        importance=Importance.MEDIUM,
        ocr_mode="auto",
        status=DocumentStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_document_high_importance() -> Document:
    """Create a high importance document"""
    return Document(
        id=2,
        title="Contract Document",
        original_filename="contract.pdf",
        file_path="documents/contract.pdf",
        file_size=2048,
        mime_type="application/pdf",
        page_count=5,
        department="Legal",
        doc_type="contract",
        importance=Importance.HIGH,
        ocr_mode="auto",
        status=DocumentStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_document_low_importance_large() -> Document:
    """Create a low importance large document"""
    return Document(
        id=3,
        title="Archive Document",
        original_filename="archive.pdf",
        file_path="documents/archive.pdf",
        file_size=10240,
        mime_type="application/pdf",
        page_count=250,
        department="Archive",
        doc_type="archive",
        importance=Importance.LOW,
        ocr_mode="auto",
        status=DocumentStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_page() -> DocumentPage:
    """Create a sample page for testing"""
    return DocumentPage(
        id=1,
        document_id=1,
        page_no=1,
        image_path="pages/1/page_1.png",
        width=800,
        height=1200,
        raw_text="Sample text content",
        confidence=0.95,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_block() -> DocumentBlock:
    """Create a sample block for testing"""
    return DocumentBlock(
        id=1,
        page_id=1,
        block_order=0,
        block_type=BlockType.TEXT,
        bbox=[0.1, 0.1, 0.9, 0.2],
        text="Sample block text",
        confidence=0.92,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_table_block() -> DocumentBlock:
    """Create a sample table block for testing"""
    return DocumentBlock(
        id=2,
        page_id=1,
        block_order=1,
        block_type=BlockType.TABLE,
        bbox=[0.1, 0.3, 0.9, 0.6],
        text=None,
        table_json={
            "rows": [
                ["Header 1", "Header 2", "Header 3"],
                ["Value 1", "Value 2", "Value 3"],
                ["Value 4", "Value 5", "Value 6"],
            ]
        },
        confidence=0.88,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def document_with_pages(sample_document, sample_page, sample_block, sample_table_block):
    """Create a document with pages and blocks"""
    sample_page.blocks = [sample_block, sample_table_block]
    sample_document.pages = [sample_page]
    return sample_document


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_storage_service():
    """Mock storage service"""
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="documents/uploaded.pdf")
    mock.download_file = AsyncMock(return_value=b"file content")
    mock.delete_file = AsyncMock(return_value=True)
    mock.get_presigned_url = MagicMock(return_value="http://localhost:9000/presigned-url")
    mock.file_exists = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_minio_client():
    """Mock MinIO client"""
    mock = MagicMock()
    mock.bucket_exists = MagicMock(return_value=True)
    mock.put_object = MagicMock()
    mock.get_object = MagicMock()
    mock.remove_object = MagicMock()
    mock.presigned_get_object = MagicMock(return_value="http://localhost:9000/presigned-url")
    return mock


@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    mock = MagicMock()
    mock.delay = MagicMock(return_value=MagicMock(id="task-123"))
    mock.apply_async = MagicMock(return_value=MagicMock(id="task-123"))
    return mock


# ============================================================
# Test Data Fixtures
# ============================================================

@pytest.fixture
def sample_table_json():
    """Sample table JSON data"""
    return {
        "rows": [
            ["Name", "Age", "City"],
            ["Alice", "30", "Seoul"],
            ["Bob", "25", "Busan"],
            ["Charlie", "35", "Incheon"],
        ]
    }


@pytest.fixture
def empty_table_json():
    """Empty table JSON data"""
    return {"rows": []}


@pytest.fixture
def sample_ocr_result():
    """Sample OCR result data"""
    return {
        "page_no": 1,
        "width": 800,
        "height": 1200,
        "blocks": [
            {
                "text": "Hello World",
                "bbox": [0.1, 0.1, 0.5, 0.15],
                "confidence": 0.95,
                "block_type": "text"
            },
            {
                "text": "This is a test",
                "bbox": [0.1, 0.2, 0.8, 0.25],
                "confidence": 0.92,
                "block_type": "text"
            }
        ],
        "raw_text": "Hello World\nThis is a test",
        "confidence": 0.935
    }
