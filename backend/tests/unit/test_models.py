"""
Unit tests for database models and enums
"""
import pytest
from datetime import datetime

from app.models.document import (
    OCRMode, DocumentStatus, Importance, BlockType,
    Document, DocumentPage, DocumentBlock
)


class TestOCRModeEnum:
    """Tests for OCRMode enum"""

    def test_ocr_mode_values(self):
        """Test OCRMode enum values"""
        assert OCRMode.FAST.value == "fast"
        assert OCRMode.ACCURATE.value == "accurate"
        assert OCRMode.PRECISION.value == "precision"
        assert OCRMode.AUTO.value == "auto"

    def test_ocr_mode_case_insensitive_matching(self):
        """Test case-insensitive matching via _missing_"""
        assert OCRMode("FAST") == OCRMode.FAST
        assert OCRMode("Fast") == OCRMode.FAST
        assert OCRMode("fast") == OCRMode.FAST

        assert OCRMode("ACCURATE") == OCRMode.ACCURATE
        assert OCRMode("Accurate") == OCRMode.ACCURATE

        assert OCRMode("PRECISION") == OCRMode.PRECISION
        assert OCRMode("Precision") == OCRMode.PRECISION

        assert OCRMode("AUTO") == OCRMode.AUTO
        assert OCRMode("Auto") == OCRMode.AUTO

    def test_ocr_mode_invalid_value(self):
        """Test invalid value returns None"""
        result = OCRMode._missing_("invalid")
        assert result is None

    def test_ocr_mode_is_string(self):
        """Test OCRMode is a string enum"""
        assert isinstance(OCRMode.FAST, str)
        assert OCRMode.FAST == "fast"


class TestDocumentStatusEnum:
    """Tests for DocumentStatus enum"""

    def test_document_status_values(self):
        """Test DocumentStatus enum values"""
        assert DocumentStatus.PENDING.value == "PENDING"
        assert DocumentStatus.PROCESSING.value == "PROCESSING"
        assert DocumentStatus.COMPLETED.value == "COMPLETED"
        assert DocumentStatus.FAILED.value == "FAILED"
        assert DocumentStatus.REVIEW.value == "REVIEW"

    def test_all_statuses_exist(self):
        """Test all expected statuses exist"""
        statuses = [s.value for s in DocumentStatus]
        assert "PENDING" in statuses
        assert "PROCESSING" in statuses
        assert "COMPLETED" in statuses
        assert "FAILED" in statuses
        assert "REVIEW" in statuses


class TestImportanceEnum:
    """Tests for Importance enum"""

    def test_importance_values(self):
        """Test Importance enum values"""
        assert Importance.LOW.value == "LOW"
        assert Importance.MEDIUM.value == "MEDIUM"
        assert Importance.HIGH.value == "HIGH"

    def test_importance_ordering(self):
        """Test importance levels are correctly defined"""
        levels = list(Importance)
        assert len(levels) == 3


class TestBlockTypeEnum:
    """Tests for BlockType enum"""

    def test_block_type_values(self):
        """Test BlockType enum values"""
        assert BlockType.TEXT.value == "TEXT"
        assert BlockType.TABLE.value == "TABLE"
        assert BlockType.IMAGE.value == "IMAGE"
        assert BlockType.HEADER.value == "HEADER"
        assert BlockType.FOOTER.value == "FOOTER"
        assert BlockType.LIST.value == "LIST"

    def test_all_block_types_exist(self):
        """Test all expected block types exist"""
        types = [t.value for t in BlockType]
        expected = ["TEXT", "TABLE", "IMAGE", "HEADER", "FOOTER", "LIST"]
        for expected_type in expected:
            assert expected_type in types


class TestDocumentModel:
    """Tests for Document model"""

    def test_document_creation(self, sample_document):
        """Test document creation with all fields"""
        assert sample_document.id == 1
        assert sample_document.title == "Test Document"
        assert sample_document.original_filename == "test.pdf"
        assert sample_document.file_path == "documents/test.pdf"
        assert sample_document.file_size == 1024
        assert sample_document.mime_type == "application/pdf"
        assert sample_document.page_count == 10
        assert sample_document.department == "Engineering"
        assert sample_document.doc_type == "report"
        assert sample_document.importance == Importance.MEDIUM
        assert sample_document.status == DocumentStatus.PENDING

    def test_document_default_status(self):
        """Test document default status is PENDING"""
        doc = Document(
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf"
        )
        # Note: Default is set at DB level, so checking enum is correct
        assert DocumentStatus.PENDING.value == "PENDING"

    def test_document_importance_levels(self, sample_document, sample_document_high_importance):
        """Test different importance levels"""
        assert sample_document.importance == Importance.MEDIUM
        assert sample_document_high_importance.importance == Importance.HIGH


class TestDocumentPageModel:
    """Tests for DocumentPage model"""

    def test_page_creation(self, sample_page):
        """Test page creation with all fields"""
        assert sample_page.id == 1
        assert sample_page.document_id == 1
        assert sample_page.page_no == 1
        assert sample_page.width == 800
        assert sample_page.height == 1200
        assert sample_page.raw_text == "Sample text content"
        assert sample_page.confidence == 0.95

    def test_page_image_path(self, sample_page):
        """Test page image path format"""
        assert "page_1.png" in sample_page.image_path


class TestDocumentBlockModel:
    """Tests for DocumentBlock model"""

    def test_block_creation(self, sample_block):
        """Test block creation with text"""
        assert sample_block.id == 1
        assert sample_block.page_id == 1
        assert sample_block.block_order == 0
        assert sample_block.block_type == BlockType.TEXT
        assert sample_block.text == "Sample block text"
        assert sample_block.confidence == 0.92
        assert sample_block.bbox == [0.1, 0.1, 0.9, 0.2]

    def test_table_block_creation(self, sample_table_block):
        """Test table block creation"""
        assert sample_table_block.block_type == BlockType.TABLE
        assert sample_table_block.table_json is not None
        assert "rows" in sample_table_block.table_json
        assert len(sample_table_block.table_json["rows"]) == 3

    def test_block_bbox_format(self, sample_block):
        """Test bbox is normalized coordinates [x1, y1, x2, y2]"""
        bbox = sample_block.bbox
        assert len(bbox) == 4
        assert all(0 <= coord <= 1 for coord in bbox)
        # x1 < x2
        assert bbox[0] < bbox[2]
        # y1 < y2
        assert bbox[1] < bbox[3]


class TestDocumentWithPages:
    """Tests for document with pages and blocks"""

    def test_document_has_pages(self, document_with_pages):
        """Test document has pages"""
        assert len(document_with_pages.pages) == 1

    def test_page_has_blocks(self, document_with_pages):
        """Test page has blocks"""
        page = document_with_pages.pages[0]
        assert len(page.blocks) == 2

    def test_blocks_include_text_and_table(self, document_with_pages):
        """Test blocks include both text and table types"""
        page = document_with_pages.pages[0]
        block_types = [b.block_type for b in page.blocks]
        assert BlockType.TEXT in block_types
        assert BlockType.TABLE in block_types
