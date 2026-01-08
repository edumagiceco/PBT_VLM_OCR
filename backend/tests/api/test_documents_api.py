"""
API tests for document endpoints
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from io import BytesIO

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.document import Document, DocumentPage, DocumentBlock, DocumentStatus, OCRMode, Importance, BlockType
from app.schemas.document import OCRModeRecommendation


# Create test app
def create_test_app():
    """Create FastAPI test application"""
    from app.api.v1.documents import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/documents")
    return app


@pytest.fixture
def client():
    """Create test client"""
    app = create_test_app()
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_document_response():
    """Sample document for API responses"""
    return Document(
        id=1,
        title="Test Document",
        original_filename="test.pdf",
        file_path="documents/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        page_count=5,
        department="Engineering",
        doc_type="report",
        importance=Importance.MEDIUM,
        ocr_mode=OCRMode.AUTO,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestGetProcessingQueue:
    """Tests for GET /queue endpoint"""

    def test_get_queue_success(self):
        """Test getting processing queue"""
        from app.api.v1.documents import router
        from app.db.session import get_db

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/documents")

        # Create mock DB session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        # Override get_db dependency
        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/api/v1/documents/queue")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "processing" in data
        assert "completed" in data
        assert "failed" in data
        assert "items" in data


class TestUploadDocument:
    """Tests for POST / endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.create_document")
    def test_upload_document_success(self, mock_create, mock_get_db, client, sample_document_response):
        """Test successful document upload"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        sample_document_response.pages = []
        mock_create.return_value = sample_document_response

        files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
        data = {
            "title": "Test Document",
            "department": "Engineering",
            "importance": "MEDIUM",
            "ocr_mode": "auto",
        }

        response = client.post("/api/v1/documents", files=files, data=data)

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Test Document"
        mock_create.assert_called_once()

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.create_document")
    def test_upload_document_without_title(self, mock_create, mock_get_db, client, sample_document_response):
        """Test upload without title uses filename"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        sample_document_response.pages = []
        mock_create.return_value = sample_document_response

        files = {"file": ("mydoc.pdf", b"PDF content", "application/pdf")}

        response = client.post("/api/v1/documents", files=files)

        assert response.status_code == 201


class TestListDocuments:
    """Tests for GET / endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.list_documents")
    def test_list_documents_success(self, mock_list, mock_get_db, client):
        """Test listing documents"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_list.return_value = MagicMock(
            total=0,
            page=1,
            page_size=20,
            items=[],
        )

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.list_documents")
    def test_list_documents_with_pagination(self, mock_list, mock_get_db, client):
        """Test listing documents with pagination"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_list.return_value = MagicMock(
            total=50,
            page=2,
            page_size=10,
            items=[],
        )

        response = client.get("/api/v1/documents?page=2&page_size=10")

        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.list_documents")
    def test_list_documents_with_search(self, mock_list, mock_get_db, client):
        """Test listing documents with search"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_list.return_value = MagicMock(
            total=5,
            page=1,
            page_size=20,
            items=[],
        )

        response = client.get("/api/v1/documents?search=contract")

        assert response.status_code == 200
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["search"] == "contract"


class TestGetDocument:
    """Tests for GET /{document_id} endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    def test_get_document_success(self, mock_get, mock_get_db, client, sample_document_response):
        """Test getting a document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        sample_document_response.pages = []
        mock_get.return_value = sample_document_response

        response = client.get("/api/v1/documents/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Document"

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    def test_get_document_not_found(self, mock_get, mock_get_db, client):
        """Test getting non-existent document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get.return_value = None

        response = client.get("/api/v1/documents/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found"


class TestUpdateDocument:
    """Tests for PATCH /{document_id} endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.update_document")
    def test_update_document_success(self, mock_update, mock_get_db, client, sample_document_response):
        """Test updating a document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        sample_document_response.title = "Updated Title"
        sample_document_response.pages = []
        mock_update.return_value = sample_document_response

        response = client.patch(
            "/api/v1/documents/1",
            json={"title": "Updated Title"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.update_document")
    def test_update_document_not_found(self, mock_update, mock_get_db, client):
        """Test updating non-existent document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_update.return_value = None

        response = client.patch(
            "/api/v1/documents/99999",
            json={"title": "Updated Title"}
        )

        assert response.status_code == 404


class TestDeleteDocument:
    """Tests for DELETE /{document_id} endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.delete_document")
    def test_delete_document_success(self, mock_delete, mock_get_db, client):
        """Test deleting a document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_delete.return_value = True

        response = client.delete("/api/v1/documents/1")

        assert response.status_code == 204

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.delete_document")
    def test_delete_document_not_found(self, mock_delete, mock_get_db, client):
        """Test deleting non-existent document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_delete.return_value = False

        response = client.delete("/api/v1/documents/99999")

        assert response.status_code == 404


class TestRecommendOcrMode:
    """Tests for GET /{document_id}/recommend-ocr endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    @patch("app.api.v1.documents.ocr_service.recommend_ocr_mode")
    def test_recommend_ocr_mode_success(self, mock_recommend, mock_get_doc, mock_get_db, client, sample_document_response):
        """Test OCR mode recommendation"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_doc.return_value = sample_document_response
        mock_recommend.return_value = OCRModeRecommendation(
            recommended_mode=OCRMode.ACCURATE,
            precision_score=45,
            reasons=["Test reason"],
        )

        response = client.get("/api/v1/documents/1/recommend-ocr")

        assert response.status_code == 200
        data = response.json()
        assert data["recommended_mode"] == "accurate"
        assert data["precision_score"] == 45

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    def test_recommend_ocr_mode_not_found(self, mock_get_doc, mock_get_db, client):
        """Test recommendation for non-existent document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_doc.return_value = None

        response = client.get("/api/v1/documents/99999/recommend-ocr")

        assert response.status_code == 404


class TestReprocessDocument:
    """Tests for POST /{document_id}/reprocess endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.reprocess_document")
    def test_reprocess_document_success(self, mock_reprocess, mock_get_db, client, sample_document_response):
        """Test document reprocessing"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        sample_document_response.status = DocumentStatus.PENDING
        sample_document_response.pages = []
        mock_reprocess.return_value = sample_document_response

        response = client.post("/api/v1/documents/1/reprocess")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.reprocess_document")
    def test_reprocess_with_ocr_mode(self, mock_reprocess, mock_get_db, client, sample_document_response):
        """Test reprocessing with specific OCR mode"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        sample_document_response.ocr_mode = OCRMode.PRECISION
        sample_document_response.pages = []
        mock_reprocess.return_value = sample_document_response

        response = client.post("/api/v1/documents/1/reprocess?ocr_mode=precision")

        assert response.status_code == 200
        mock_reprocess.assert_called_once()


class TestDownloadDocument:
    """Tests for GET /{document_id}/download endpoint"""

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    @patch("app.api.v1.documents.export_service.export_document")
    def test_download_markdown(self, mock_export, mock_get_doc, mock_get_db, client, sample_document_response):
        """Test downloading as markdown"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_doc.return_value = sample_document_response
        mock_export.return_value = (b"# Test Document", "text/markdown", "Test_Document.md")

        response = client.get("/api/v1/documents/1/download?format=md")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    @patch("app.api.v1.documents.export_service.export_document")
    def test_download_json(self, mock_export, mock_get_doc, mock_get_db, client, sample_document_response):
        """Test downloading as JSON"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_doc.return_value = sample_document_response
        mock_export.return_value = (b'{"document": {}}', "application/json", "Test_Document.json")

        response = client.get("/api/v1/documents/1/download?format=json")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    @patch("app.api.v1.documents.export_service.export_document")
    def test_download_html(self, mock_export, mock_get_doc, mock_get_db, client, sample_document_response):
        """Test downloading as HTML"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_doc.return_value = sample_document_response
        mock_export.return_value = (b"<!DOCTYPE html>", "text/html", "Test_Document.html")

        response = client.get("/api/v1/documents/1/download?format=html")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @patch("app.api.v1.documents.get_db")
    @patch("app.api.v1.documents.document_service.get_document")
    def test_download_not_found(self, mock_get_doc, mock_get_db, client):
        """Test downloading non-existent document"""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_doc.return_value = None

        response = client.get("/api/v1/documents/99999/download")

        assert response.status_code == 404

    def test_download_invalid_format(self, client):
        """Test downloading with invalid format"""
        # FastAPI's Query regex validation should reject this
        response = client.get("/api/v1/documents/1/download?format=pdf")

        assert response.status_code == 422  # Validation error
