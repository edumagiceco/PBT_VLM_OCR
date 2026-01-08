"""
Unit tests for document service
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from io import BytesIO

from app.models.document import Document, DocumentStatus, OCRMode, Importance
from app.schemas.document import DocumentCreate, DocumentUpdate, BlockUpdate
from app.services.document_service import (
    _get_ocr_queue,
    create_document,
    get_document,
    list_documents,
    update_document,
    delete_document,
    reprocess_document,
    update_block,
    get_document_statistics,
)


class TestGetOcrQueue:
    """Tests for _get_ocr_queue function"""

    def test_fast_mode_returns_fast_queue(self):
        """Test FAST mode returns fast_ocr queue"""
        assert _get_ocr_queue(OCRMode.FAST) == "fast_ocr"
        assert _get_ocr_queue("fast") == "fast_ocr"

    def test_accurate_mode_returns_accurate_queue(self):
        """Test ACCURATE mode returns accurate_ocr queue"""
        assert _get_ocr_queue(OCRMode.ACCURATE) == "accurate_ocr"
        assert _get_ocr_queue("accurate") == "accurate_ocr"

    def test_precision_mode_returns_precision_queue(self):
        """Test PRECISION mode returns precision_ocr queue"""
        assert _get_ocr_queue(OCRMode.PRECISION) == "precision_ocr"
        assert _get_ocr_queue("precision") == "precision_ocr"

    def test_auto_mode_returns_fast_queue(self):
        """Test AUTO mode returns fast_ocr queue (default)"""
        assert _get_ocr_queue(OCRMode.AUTO) == "fast_ocr"
        assert _get_ocr_queue("auto") == "fast_ocr"

    def test_unknown_mode_returns_fast_queue(self):
        """Test unknown mode returns fast_ocr queue (fallback)"""
        assert _get_ocr_queue("unknown") == "fast_ocr"

    def test_case_insensitive_mode(self):
        """Test mode string is case-insensitive"""
        assert _get_ocr_queue("FAST") == "fast_ocr"
        assert _get_ocr_queue("Fast") == "fast_ocr"


class TestCreateDocument:
    """Tests for create_document function"""

    @pytest.mark.asyncio
    @patch("app.services.document_service.storage_service")
    @patch("app.workers.tasks.process_document")
    async def test_create_document_success(self, mock_task, mock_storage, in_memory_db):
        """Test successful document creation"""
        # Setup mocks
        mock_storage.upload_document.return_value = ("documents/test.pdf", 1024)
        mock_task.apply_async.return_value = MagicMock(id="task-123")

        # Create mock file
        mock_file = MagicMock()
        mock_file.read = AsyncMock(return_value=b"file content")
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"

        # Create document
        doc_create = DocumentCreate(
            title="Test Document",
            department="Engineering",
            doc_type="report",
            importance=Importance.MEDIUM,
            ocr_mode=OCRMode.AUTO,
        )

        result = await create_document(in_memory_db, mock_file, doc_create)

        # Verify
        assert result.title == "Test Document"
        assert result.department == "Engineering"
        assert result.status == DocumentStatus.PENDING
        mock_storage.upload_document.assert_called_once()
        mock_task.apply_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.document_service.storage_service")
    @patch("app.workers.tasks.process_document")
    async def test_create_document_with_precision_mode(self, mock_task, mock_storage, in_memory_db):
        """Test document creation with precision OCR mode uses correct queue"""
        mock_storage.upload_document.return_value = ("documents/test.pdf", 1024)
        mock_task.apply_async.return_value = MagicMock(id="task-123")

        mock_file = MagicMock()
        mock_file.read = AsyncMock(return_value=b"file content")
        mock_file.filename = "contract.pdf"
        mock_file.content_type = "application/pdf"

        doc_create = DocumentCreate(
            title="Contract",
            ocr_mode=OCRMode.PRECISION,
        )

        await create_document(in_memory_db, mock_file, doc_create)

        # Verify precision queue is used
        mock_task.apply_async.assert_called_once()
        call_kwargs = mock_task.apply_async.call_args.kwargs
        assert call_kwargs["queue"] == "precision_ocr"


class TestGetDocument:
    """Tests for get_document function"""

    @pytest.mark.asyncio
    async def test_get_existing_document(self, in_memory_db, sample_document):
        """Test getting an existing document"""
        in_memory_db.add(sample_document)
        in_memory_db.commit()

        result = await get_document(in_memory_db, sample_document.id)

        assert result is not None
        assert result.id == sample_document.id
        assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, in_memory_db):
        """Test getting a non-existent document returns None"""
        result = await get_document(in_memory_db, 99999)
        assert result is None


class TestListDocuments:
    """Tests for list_documents function"""

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, in_memory_db):
        """Test listing documents when none exist"""
        result = await list_documents(in_memory_db)

        assert result.total == 0
        assert result.page == 1
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_documents_with_data(self, in_memory_db, sample_document):
        """Test listing documents with data"""
        in_memory_db.add(sample_document)
        in_memory_db.commit()

        result = await list_documents(in_memory_db)

        assert result.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, in_memory_db):
        """Test document pagination"""
        # Create multiple documents
        for i in range(25):
            doc = Document(
                title=f"Document {i}",
                original_filename=f"doc{i}.pdf",
                file_path=f"documents/doc{i}.pdf",
                status=DocumentStatus.PENDING,
            )
            in_memory_db.add(doc)
        in_memory_db.commit()

        result = await list_documents(in_memory_db, page=1, page_size=10)

        assert result.total == 25
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.items) == 10

    @pytest.mark.asyncio
    async def test_list_documents_search(self, in_memory_db):
        """Test document search by title"""
        doc1 = Document(
            title="Important Report",
            original_filename="report.pdf",
            file_path="documents/report.pdf",
            status=DocumentStatus.PENDING,
        )
        doc2 = Document(
            title="Regular Document",
            original_filename="regular.pdf",
            file_path="documents/regular.pdf",
            status=DocumentStatus.PENDING,
        )
        in_memory_db.add_all([doc1, doc2])
        in_memory_db.commit()

        result = await list_documents(in_memory_db, search="Important")

        assert result.total == 1
        assert result.items[0].title == "Important Report"

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_department(self, in_memory_db):
        """Test filtering by department"""
        doc1 = Document(
            title="Doc 1",
            original_filename="doc1.pdf",
            file_path="documents/doc1.pdf",
            department="Engineering",
            status=DocumentStatus.PENDING,
        )
        doc2 = Document(
            title="Doc 2",
            original_filename="doc2.pdf",
            file_path="documents/doc2.pdf",
            department="Sales",
            status=DocumentStatus.PENDING,
        )
        in_memory_db.add_all([doc1, doc2])
        in_memory_db.commit()

        result = await list_documents(in_memory_db, department="Engineering")

        assert result.total == 1
        assert result.items[0].department == "Engineering"


class TestUpdateDocument:
    """Tests for update_document function"""

    @pytest.mark.asyncio
    async def test_update_document_success(self, in_memory_db, sample_document):
        """Test successful document update"""
        in_memory_db.add(sample_document)
        in_memory_db.commit()

        update_data = DocumentUpdate(title="Updated Title", department="Sales")
        result = await update_document(in_memory_db, sample_document.id, update_data)

        assert result is not None
        assert result.title == "Updated Title"
        assert result.department == "Sales"

    @pytest.mark.asyncio
    async def test_update_document_partial(self, in_memory_db, sample_document):
        """Test partial document update"""
        in_memory_db.add(sample_document)
        in_memory_db.commit()
        original_department = sample_document.department

        update_data = DocumentUpdate(title="New Title")
        result = await update_document(in_memory_db, sample_document.id, update_data)

        assert result.title == "New Title"
        assert result.department == original_department

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, in_memory_db):
        """Test updating non-existent document returns None"""
        update_data = DocumentUpdate(title="New Title")
        result = await update_document(in_memory_db, 99999, update_data)

        assert result is None


class TestDeleteDocument:
    """Tests for delete_document function"""

    @pytest.mark.asyncio
    @patch("app.services.document_service.storage_service")
    async def test_delete_document_success(self, mock_storage, in_memory_db, sample_document):
        """Test successful document deletion"""
        in_memory_db.add(sample_document)
        in_memory_db.commit()
        doc_id = sample_document.id

        result = await delete_document(in_memory_db, doc_id)

        assert result is True
        mock_storage.delete_file.assert_called_once()
        mock_storage.delete_document_files.assert_called_once_with(doc_id)

        # Verify document is deleted
        deleted = await get_document(in_memory_db, doc_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, in_memory_db):
        """Test deleting non-existent document returns False"""
        result = await delete_document(in_memory_db, 99999)
        assert result is False


class TestReprocessDocument:
    """Tests for reprocess_document function"""

    @pytest.mark.asyncio
    @patch("app.services.document_service.storage_service")
    @patch("app.workers.tasks.process_document")
    async def test_reprocess_document_success(self, mock_task, mock_storage, in_memory_db, sample_document):
        """Test successful document reprocessing"""
        sample_document.status = DocumentStatus.COMPLETED
        in_memory_db.add(sample_document)
        in_memory_db.commit()

        mock_task.apply_async.return_value = MagicMock(id="task-456")

        result = await reprocess_document(in_memory_db, sample_document.id)

        assert result is not None
        assert result.status == DocumentStatus.PENDING
        assert result.error_message is None
        mock_storage.delete_document_files.assert_called_once()
        mock_task.apply_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.document_service.storage_service")
    @patch("app.workers.tasks.process_document")
    async def test_reprocess_with_new_ocr_mode(self, mock_task, mock_storage, in_memory_db, sample_document):
        """Test reprocessing with new OCR mode"""
        in_memory_db.add(sample_document)
        in_memory_db.commit()

        mock_task.apply_async.return_value = MagicMock(id="task-456")

        result = await reprocess_document(
            in_memory_db, sample_document.id, ocr_mode=OCRMode.PRECISION
        )

        assert result.ocr_mode == OCRMode.PRECISION
        call_kwargs = mock_task.apply_async.call_args.kwargs
        assert call_kwargs["queue"] == "precision_ocr"

    @pytest.mark.asyncio
    async def test_reprocess_nonexistent_document(self, in_memory_db):
        """Test reprocessing non-existent document returns None"""
        result = await reprocess_document(in_memory_db, 99999)
        assert result is None


class TestGetDocumentStatistics:
    """Tests for get_document_statistics function"""

    @pytest.mark.asyncio
    async def test_statistics_empty_db(self, in_memory_db):
        """Test statistics with empty database"""
        result = await get_document_statistics(in_memory_db)

        assert result["total"] == 0
        assert result["by_status"]["PENDING"] == 0
        assert result["by_status"]["COMPLETED"] == 0

    @pytest.mark.asyncio
    async def test_statistics_with_documents(self, in_memory_db):
        """Test statistics with documents"""
        docs = [
            Document(
                title="Doc 1",
                original_filename="doc1.pdf",
                file_path="documents/doc1.pdf",
                status=DocumentStatus.PENDING,
                ocr_mode=OCRMode.FAST,
            ),
            Document(
                title="Doc 2",
                original_filename="doc2.pdf",
                file_path="documents/doc2.pdf",
                status=DocumentStatus.COMPLETED,
                ocr_mode=OCRMode.PRECISION,
            ),
            Document(
                title="Doc 3",
                original_filename="doc3.pdf",
                file_path="documents/doc3.pdf",
                status=DocumentStatus.PENDING,
                ocr_mode=OCRMode.FAST,
            ),
        ]
        in_memory_db.add_all(docs)
        in_memory_db.commit()

        result = await get_document_statistics(in_memory_db)

        assert result["total"] == 3
        assert result["by_status"]["PENDING"] == 2
        assert result["by_status"]["COMPLETED"] == 1
