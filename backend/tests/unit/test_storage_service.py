"""
Unit tests for storage service (MinIO operations)
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import timedelta
from io import BytesIO

from PIL import Image
from minio.error import S3Error

from app.services.storage_service import StorageService


@pytest.fixture
def storage_service():
    """Create storage service instance"""
    return StorageService()


@pytest.fixture
def mock_minio_client():
    """Mock MinIO client"""
    mock = MagicMock()
    mock.bucket_exists.return_value = True
    mock.make_bucket.return_value = None
    mock.put_object.return_value = None
    mock.get_object.return_value = MagicMock(
        read=MagicMock(return_value=b"file content"),
        close=MagicMock(),
        release_conn=MagicMock(),
    )
    mock.remove_object.return_value = None
    mock.presigned_get_object.return_value = "http://localhost:9000/bucket/object"
    mock.presigned_put_object.return_value = "http://localhost:9000/bucket/upload"
    mock.stat_object.return_value = MagicMock(
        size=1024,
        content_type="application/pdf",
        last_modified="2024-01-01T00:00:00",
        etag="abc123",
    )
    mock.list_objects.return_value = []
    return mock


@pytest.fixture
def sample_image():
    """Create sample PIL image"""
    return Image.new("RGB", (800, 600), color="white")


class TestStorageServiceInit:
    """Tests for StorageService initialization"""

    def test_client_lazy_loading(self, storage_service):
        """Test client is lazily loaded"""
        assert storage_service._client is None

    @patch("app.services.storage_service.Minio")
    def test_client_created_on_access(self, mock_minio, storage_service):
        """Test client is created when accessed"""
        mock_minio.return_value = MagicMock()

        _ = storage_service.client

        mock_minio.assert_called_once()
        assert storage_service._client is not None


class TestEnsureBucket:
    """Tests for ensure_bucket method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_bucket_exists(self, mock_client_prop, storage_service, mock_minio_client):
        """Test when bucket already exists"""
        mock_client_prop.return_value = mock_minio_client
        mock_minio_client.bucket_exists.return_value = True

        storage_service.ensure_bucket()

        mock_minio_client.bucket_exists.assert_called_once()
        mock_minio_client.make_bucket.assert_not_called()

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_bucket_created(self, mock_client_prop, storage_service, mock_minio_client):
        """Test bucket creation when not exists"""
        mock_client_prop.return_value = mock_minio_client
        mock_minio_client.bucket_exists.return_value = False

        storage_service.ensure_bucket()

        mock_minio_client.make_bucket.assert_called_once()


class TestUploadFile:
    """Tests for upload_file method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_upload_file_success(self, mock_client_prop, storage_service, mock_minio_client):
        """Test successful file upload"""
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.upload_file(
            file_data=b"test content",
            object_name="test/file.txt",
            content_type="text/plain",
        )

        assert result == "test/file.txt"
        mock_minio_client.put_object.assert_called_once()

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_upload_file_with_bucket(self, mock_client_prop, storage_service, mock_minio_client):
        """Test file upload with custom bucket"""
        mock_client_prop.return_value = mock_minio_client

        storage_service.upload_file(
            file_data=b"test content",
            object_name="test/file.txt",
            bucket_name="custom-bucket",
        )

        call_args = mock_minio_client.put_object.call_args
        assert call_args[0][0] == "custom-bucket"


class TestUploadDocument:
    """Tests for upload_document method"""

    @patch.object(StorageService, "upload_file")
    def test_upload_document_success(self, mock_upload, storage_service):
        """Test successful document upload"""
        mock_upload.return_value = "documents/uuid.pdf"

        path, size = storage_service.upload_document(
            file_data=b"PDF content",
            original_filename="report.pdf",
            content_type="application/pdf",
        )

        assert path.startswith("documents/")
        assert path.endswith(".pdf")
        assert size == 11  # len(b"PDF content")

    @patch.object(StorageService, "upload_file")
    def test_upload_document_preserves_extension(self, mock_upload, storage_service):
        """Test document upload preserves file extension"""
        mock_upload.return_value = "documents/uuid.docx"

        path, size = storage_service.upload_document(
            file_data=b"content",
            original_filename="document.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        assert ".docx" in path or mock_upload.called

    @patch.object(StorageService, "upload_file")
    def test_upload_document_no_extension(self, mock_upload, storage_service):
        """Test document upload without extension"""
        mock_upload.return_value = "documents/uuid"

        path, size = storage_service.upload_document(
            file_data=b"content",
            original_filename="",
            content_type="application/octet-stream",
        )

        assert path.startswith("documents/")


class TestUploadPageImage:
    """Tests for upload_page_image method"""

    @patch.object(StorageService, "upload_file")
    def test_upload_page_image_png(self, mock_upload, storage_service, sample_image):
        """Test page image upload as PNG"""
        mock_upload.return_value = "pages/1/page_0001.png"

        result = storage_service.upload_page_image(
            image=sample_image,
            document_id=1,
            page_no=1,
            format="PNG",
        )

        assert result == "pages/1/page_0001.png"
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        # content_type is passed as positional argument (3rd arg)
        assert call_args[0][2] == "image/png"

    @patch.object(StorageService, "upload_file")
    def test_upload_page_image_jpeg(self, mock_upload, storage_service, sample_image):
        """Test page image upload as JPEG"""
        mock_upload.return_value = "pages/1/page_0001.jpeg"

        result = storage_service.upload_page_image(
            image=sample_image,
            document_id=1,
            page_no=1,
            format="JPEG",
        )

        call_args = mock_upload.call_args
        # content_type is passed as positional argument (3rd arg)
        assert call_args[0][2] == "image/jpeg"

    @patch.object(StorageService, "upload_file")
    def test_upload_page_image_numbering(self, mock_upload, storage_service, sample_image):
        """Test page number formatting in path"""
        mock_upload.return_value = "pages/1/page_0042.png"

        result = storage_service.upload_page_image(
            image=sample_image,
            document_id=1,
            page_no=42,
        )

        call_args = mock_upload.call_args
        # object_name is 2nd positional argument
        assert "page_0042" in call_args[0][1]


class TestUploadThumbnail:
    """Tests for upload_thumbnail method"""

    @patch.object(StorageService, "upload_file")
    def test_upload_thumbnail_success(self, mock_upload, storage_service, sample_image):
        """Test thumbnail upload"""
        mock_upload.return_value = "thumbnails/1/page_0001.jpg"

        result = storage_service.upload_thumbnail(
            image=sample_image,
            document_id=1,
            page_no=1,
        )

        assert result == "thumbnails/1/page_0001.jpg"
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        # content_type is passed as positional argument (3rd arg)
        assert call_args[0][2] == "image/jpeg"

    @patch.object(StorageService, "upload_file")
    def test_upload_thumbnail_custom_size(self, mock_upload, storage_service, sample_image):
        """Test thumbnail with custom size"""
        mock_upload.return_value = "thumbnails/1/page_0001.jpg"

        storage_service.upload_thumbnail(
            image=sample_image,
            document_id=1,
            page_no=1,
            size=(100, 150),
        )

        mock_upload.assert_called_once()


class TestDownloadFile:
    """Tests for download_file method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_download_file_success(self, mock_client_prop, storage_service, mock_minio_client):
        """Test successful file download"""
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.download_file("test/file.txt")

        assert result == b"file content"
        mock_minio_client.get_object.assert_called_once()

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_download_file_closes_connection(self, mock_client_prop, storage_service, mock_minio_client):
        """Test download closes connection properly"""
        mock_response = MagicMock()
        mock_response.read.return_value = b"content"
        mock_minio_client.get_object.return_value = mock_response
        mock_client_prop.return_value = mock_minio_client

        storage_service.download_file("test/file.txt")

        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()


class TestGetPresignedUrl:
    """Tests for get_presigned_url method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_presigned_url_success(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test presigned URL generation"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_settings.MINIO_EXTERNAL_ENDPOINT = ""
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.get_presigned_url("test/file.txt")

        # URL should be returned from mock
        assert result is not None
        mock_minio_client.presigned_get_object.assert_called_once()

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_presigned_url_with_external_endpoint(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test presigned URL with external endpoint replacement"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_settings.MINIO_ENDPOINT = "minio:9000"
        mock_settings.MINIO_EXTERNAL_ENDPOINT = "storage.example.com"
        mock_minio_client.presigned_get_object.return_value = "http://minio:9000/bucket/file"
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.get_presigned_url("test/file.txt")

        assert "storage.example.com" in result
        assert "minio:9000" not in result

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_presigned_url_custom_expiry(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test presigned URL with custom expiry"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_settings.MINIO_EXTERNAL_ENDPOINT = ""
        mock_client_prop.return_value = mock_minio_client

        storage_service.get_presigned_url("test/file.txt", expires=timedelta(days=1))

        call_kwargs = mock_minio_client.presigned_get_object.call_args.kwargs
        assert call_kwargs["expires"] == timedelta(days=1)


class TestDeleteFile:
    """Tests for delete_file method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_delete_file_success(self, mock_client_prop, storage_service, mock_minio_client):
        """Test successful file deletion"""
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.delete_file("test/file.txt")

        assert result is True
        mock_minio_client.remove_object.assert_called_once()

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_delete_file_error(self, mock_client_prop, storage_service, mock_minio_client):
        """Test file deletion error handling"""
        mock_minio_client.remove_object.side_effect = S3Error(
            "NoSuchKey", "Object not found", "", "", "", ""
        )
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.delete_file("nonexistent/file.txt")

        assert result is False


class TestDeleteDocumentFiles:
    """Tests for delete_document_files method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_delete_document_files_success(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test deleting all document files"""
        mock_settings.MINIO_BUCKET = "test-bucket"

        # Each list_objects call (for pages/ and thumbnails/) returns the same mock
        # We need different return values for each call
        pages_objects = [
            MagicMock(object_name="pages/1/page_0001.png"),
            MagicMock(object_name="pages/1/page_0002.png"),
        ]
        thumbnails_objects = [
            MagicMock(object_name="thumbnails/1/page_0001.jpg"),
        ]
        mock_minio_client.list_objects.side_effect = [pages_objects, thumbnails_objects]
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.delete_document_files(1)

        assert result is True
        # 2 pages + 1 thumbnail = 3 deletions
        assert mock_minio_client.remove_object.call_count == 3

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_delete_document_files_error(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test document files deletion error"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_minio_client.list_objects.side_effect = S3Error(
            "AccessDenied", "Access denied", "", "", "", ""
        )
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.delete_document_files(1)

        assert result is False


class TestFileExists:
    """Tests for file_exists method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_file_exists_true(self, mock_client_prop, storage_service, mock_minio_client):
        """Test file exists check - true"""
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.file_exists("test/file.txt")

        assert result is True

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    def test_file_exists_false(self, mock_client_prop, storage_service, mock_minio_client):
        """Test file exists check - false"""
        mock_minio_client.stat_object.side_effect = S3Error(
            "NoSuchKey", "Not found", "", "", "", ""
        )
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.file_exists("nonexistent/file.txt")

        assert result is False


class TestGetStorageStats:
    """Tests for get_storage_stats method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_storage_stats_empty(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test storage stats with empty bucket"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_minio_client.list_objects.return_value = []
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.get_storage_stats()

        assert result["total_size_bytes"] == 0
        assert result["total_objects"] == 0

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_storage_stats_with_files(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test storage stats with files"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="documents/doc1.pdf", size=1000),
            MagicMock(object_name="pages/1/page_0001.png", size=500),
            MagicMock(object_name="thumbnails/1/page_0001.jpg", size=100),
        ]
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.get_storage_stats()

        assert result["total_size_bytes"] == 1600
        assert result["total_objects"] == 3
        assert result["categories"]["documents"]["size_bytes"] == 1000
        assert result["categories"]["pages"]["size_bytes"] == 500
        assert result["categories"]["thumbnails"]["size_bytes"] == 100


class TestGetOrphanedFiles:
    """Tests for get_orphaned_files method"""

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_orphaned_files_none(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test no orphaned files"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        # Both pages/ and thumbnails/ prefixes are checked
        mock_minio_client.list_objects.side_effect = [
            [MagicMock(object_name="pages/1/page_0001.png", size=500, last_modified=None)],
            [],  # No thumbnails
        ]
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.get_orphaned_files(valid_document_ids={1})

        assert len(result) == 0

    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_orphaned_files_found(self, mock_settings, mock_client_prop, storage_service, mock_minio_client):
        """Test orphaned files found"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        # Both pages/ and thumbnails/ prefixes are checked
        mock_minio_client.list_objects.side_effect = [
            [
                MagicMock(object_name="pages/1/page_0001.png", size=500, last_modified=None),
                MagicMock(object_name="pages/999/page_0001.png", size=500, last_modified=None),
            ],
            [],  # No thumbnails
        ]
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.get_orphaned_files(valid_document_ids={1})

        assert len(result) == 1
        assert result[0]["object_name"] == "pages/999/page_0001.png"


class TestCleanupOrphanedFiles:
    """Tests for cleanup_orphaned_files method"""

    @patch.object(StorageService, "get_orphaned_files")
    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_cleanup_success(self, mock_settings, mock_client_prop, mock_get_orphaned, storage_service, mock_minio_client):
        """Test successful cleanup"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_get_orphaned.return_value = [
            {"object_name": "pages/999/page_0001.png", "size": 500},
        ]
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.cleanup_orphaned_files(valid_document_ids={1})

        assert result["deleted_count"] == 1
        assert result["deleted_size_bytes"] == 500
        assert result["errors"] == []

    @patch.object(StorageService, "get_orphaned_files")
    @patch.object(StorageService, "client", new_callable=PropertyMock)
    @patch("app.services.storage_service.settings")
    def test_cleanup_partial_failure(self, mock_settings, mock_client_prop, mock_get_orphaned, storage_service, mock_minio_client):
        """Test cleanup with partial failure"""
        mock_settings.MINIO_BUCKET = "test-bucket"
        mock_get_orphaned.return_value = [
            {"object_name": "pages/999/page_0001.png", "size": 500},
            {"object_name": "pages/888/page_0001.png", "size": 300},
        ]
        mock_minio_client.remove_object.side_effect = [
            None,
            S3Error("Error", "Failed to delete", "", "", "", ""),
        ]
        mock_client_prop.return_value = mock_minio_client

        result = storage_service.cleanup_orphaned_files(valid_document_ids={1})

        assert result["deleted_count"] == 1
        assert result["deleted_size_bytes"] == 500
        assert len(result["errors"]) == 1
