"""
MinIO 스토리지 서비스

파일 업로드, 다운로드, URL 생성 등 스토리지 관련 기능 제공
"""
import os
import uuid
from io import BytesIO
from datetime import timedelta
from typing import Optional, Tuple, BinaryIO

from minio import Minio
from minio.error import S3Error
from PIL import Image

from app.core.config import settings


class StorageService:
    """MinIO 스토리지 서비스"""

    def __init__(self):
        self._client: Optional[Minio] = None

    @property
    def client(self) -> Minio:
        """MinIO 클라이언트 (지연 로딩)"""
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
        return self._client

    def ensure_bucket(self, bucket_name: str = None):
        """버킷이 없으면 생성"""
        bucket = bucket_name or settings.MINIO_BUCKET
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    # =========================================
    # 파일 업로드
    # =========================================

    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
        bucket_name: str = None,
    ) -> str:
        """
        파일 업로드

        Args:
            file_data: 파일 바이트 데이터
            object_name: 저장할 객체 이름 (경로 포함)
            content_type: MIME 타입
            bucket_name: 버킷 이름 (기본값: 설정 버킷)

        Returns:
            저장된 객체 경로
        """
        bucket = bucket_name or settings.MINIO_BUCKET
        self.ensure_bucket(bucket)

        self.client.put_object(
            bucket,
            object_name,
            BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )

        return object_name

    def upload_file_stream(
        self,
        file_stream: BinaryIO,
        object_name: str,
        length: int,
        content_type: str = "application/octet-stream",
        bucket_name: str = None,
    ) -> str:
        """파일 스트림 업로드"""
        bucket = bucket_name or settings.MINIO_BUCKET
        self.ensure_bucket(bucket)

        self.client.put_object(
            bucket,
            object_name,
            file_stream,
            length=length,
            content_type=content_type,
        )

        return object_name

    def upload_document(
        self,
        file_data: bytes,
        original_filename: str,
        content_type: str,
    ) -> Tuple[str, int]:
        """
        문서 파일 업로드

        Args:
            file_data: 파일 바이트 데이터
            original_filename: 원본 파일명
            content_type: MIME 타입

        Returns:
            (저장 경로, 파일 크기)
        """
        # 고유 ID 생성
        unique_id = str(uuid.uuid4())
        ext = os.path.splitext(original_filename)[1] if original_filename else ""
        object_name = f"documents/{unique_id}{ext}"

        self.upload_file(file_data, object_name, content_type)

        return object_name, len(file_data)

    def upload_page_image(
        self,
        image: Image.Image,
        document_id: int,
        page_no: int,
        format: str = "PNG",
    ) -> str:
        """
        페이지 이미지 업로드

        Args:
            image: PIL 이미지
            document_id: 문서 ID
            page_no: 페이지 번호
            format: 이미지 포맷 (PNG, JPEG)

        Returns:
            저장된 이미지 경로
        """
        # 이미지를 바이트로 변환
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)

        # 객체 이름 생성
        ext = format.lower()
        object_name = f"pages/{document_id}/page_{page_no:04d}.{ext}"

        content_type = f"image/{ext}"
        self.upload_file(buffer.getvalue(), object_name, content_type)

        return object_name

    def upload_thumbnail(
        self,
        image: Image.Image,
        document_id: int,
        page_no: int,
        size: Tuple[int, int] = (200, 280),
    ) -> str:
        """
        썸네일 이미지 업로드

        Args:
            image: PIL 이미지
            document_id: 문서 ID
            page_no: 페이지 번호
            size: 썸네일 크기

        Returns:
            저장된 썸네일 경로
        """
        # 썸네일 생성
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)

        # 이미지를 바이트로 변환
        buffer = BytesIO()
        thumbnail.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        # 객체 이름 생성
        object_name = f"thumbnails/{document_id}/page_{page_no:04d}.jpg"

        self.upload_file(buffer.getvalue(), object_name, "image/jpeg")

        return object_name

    # =========================================
    # 파일 다운로드
    # =========================================

    def download_file(
        self,
        object_name: str,
        bucket_name: str = None,
    ) -> bytes:
        """
        파일 다운로드

        Args:
            object_name: 객체 이름
            bucket_name: 버킷 이름

        Returns:
            파일 바이트 데이터
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        response = self.client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def download_to_file(
        self,
        object_name: str,
        local_path: str,
        bucket_name: str = None,
    ) -> str:
        """
        파일을 로컬에 다운로드

        Args:
            object_name: 객체 이름
            local_path: 로컬 저장 경로
            bucket_name: 버킷 이름

        Returns:
            로컬 파일 경로
        """
        bucket = bucket_name or settings.MINIO_BUCKET
        self.client.fget_object(bucket, object_name, local_path)
        return local_path

    # =========================================
    # URL 생성
    # =========================================

    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
        bucket_name: str = None,
    ) -> str:
        """
        사전 서명된 다운로드 URL 생성

        Args:
            object_name: 객체 이름
            expires: 만료 시간
            bucket_name: 버킷 이름

        Returns:
            사전 서명된 URL (외부 접근 가능)
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        url = self.client.presigned_get_object(
            bucket,
            object_name,
            expires=expires,
        )

        # 외부 엔드포인트가 설정된 경우 내부 호스트명을 외부 호스트명으로 교체
        if settings.MINIO_EXTERNAL_ENDPOINT:
            url = url.replace(
                f"http://{settings.MINIO_ENDPOINT}",
                f"http://{settings.MINIO_EXTERNAL_ENDPOINT}"
            )
            url = url.replace(
                f"https://{settings.MINIO_ENDPOINT}",
                f"https://{settings.MINIO_EXTERNAL_ENDPOINT}"
            )

        return url

    def get_presigned_upload_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
        bucket_name: str = None,
    ) -> str:
        """
        사전 서명된 업로드 URL 생성

        Args:
            object_name: 객체 이름
            expires: 만료 시간
            bucket_name: 버킷 이름

        Returns:
            사전 서명된 URL
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        return self.client.presigned_put_object(
            bucket,
            object_name,
            expires=expires,
        )

    # =========================================
    # 파일 관리
    # =========================================

    def delete_file(
        self,
        object_name: str,
        bucket_name: str = None,
    ) -> bool:
        """
        파일 삭제

        Args:
            object_name: 객체 이름
            bucket_name: 버킷 이름

        Returns:
            성공 여부
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        try:
            self.client.remove_object(bucket, object_name)
            return True
        except S3Error:
            return False

    def delete_document_files(self, document_id: int) -> bool:
        """
        문서 관련 모든 파일 삭제

        Args:
            document_id: 문서 ID

        Returns:
            성공 여부
        """
        bucket = settings.MINIO_BUCKET
        prefixes = [
            f"pages/{document_id}/",
            f"thumbnails/{document_id}/",
        ]

        try:
            for prefix in prefixes:
                objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
                for obj in objects:
                    self.client.remove_object(bucket, obj.object_name)
            return True
        except S3Error:
            return False

    def file_exists(
        self,
        object_name: str,
        bucket_name: str = None,
    ) -> bool:
        """
        파일 존재 여부 확인

        Args:
            object_name: 객체 이름
            bucket_name: 버킷 이름

        Returns:
            존재 여부
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False

    def get_file_info(
        self,
        object_name: str,
        bucket_name: str = None,
    ) -> Optional[dict]:
        """
        파일 정보 조회

        Args:
            object_name: 객체 이름
            bucket_name: 버킷 이름

        Returns:
            파일 정보 (size, content_type, last_modified 등)
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        try:
            stat = self.client.stat_object(bucket, object_name)
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
            }
        except S3Error:
            return None

    # =========================================
    # 스토리지 통계
    # =========================================

    def get_storage_stats(self, bucket_name: str = None) -> dict:
        """
        스토리지 통계 조회

        Args:
            bucket_name: 버킷 이름

        Returns:
            스토리지 통계 정보
        """
        bucket = bucket_name or settings.MINIO_BUCKET

        stats = {
            "bucket_name": bucket,
            "total_size_bytes": 0,
            "total_objects": 0,
            "categories": {
                "documents": {"size_bytes": 0, "count": 0},
                "pages": {"size_bytes": 0, "count": 0},
                "thumbnails": {"size_bytes": 0, "count": 0},
                "other": {"size_bytes": 0, "count": 0},
            },
        }

        try:
            self.ensure_bucket(bucket)
            objects = self.client.list_objects(bucket, recursive=True)

            for obj in objects:
                size = obj.size or 0
                stats["total_size_bytes"] += size
                stats["total_objects"] += 1

                # 카테고리 분류
                if obj.object_name.startswith("documents/"):
                    stats["categories"]["documents"]["size_bytes"] += size
                    stats["categories"]["documents"]["count"] += 1
                elif obj.object_name.startswith("pages/"):
                    stats["categories"]["pages"]["size_bytes"] += size
                    stats["categories"]["pages"]["count"] += 1
                elif obj.object_name.startswith("thumbnails/"):
                    stats["categories"]["thumbnails"]["size_bytes"] += size
                    stats["categories"]["thumbnails"]["count"] += 1
                else:
                    stats["categories"]["other"]["size_bytes"] += size
                    stats["categories"]["other"]["count"] += 1

            return stats
        except S3Error as e:
            return {
                "bucket_name": bucket,
                "error": str(e),
                "total_size_bytes": 0,
                "total_objects": 0,
                "categories": stats["categories"],
            }

    def get_orphaned_files(
        self,
        valid_document_ids: set,
        bucket_name: str = None,
    ) -> list:
        """
        고아 파일 목록 조회 (DB에 없는 문서의 파일들)

        Args:
            valid_document_ids: 유효한 문서 ID 집합
            bucket_name: 버킷 이름

        Returns:
            고아 파일 목록
        """
        bucket = bucket_name or settings.MINIO_BUCKET
        orphaned = []

        try:
            # pages, thumbnails 디렉토리의 파일 확인
            for prefix in ["pages/", "thumbnails/"]:
                objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
                for obj in objects:
                    # 경로에서 문서 ID 추출 (예: pages/123/page_0001.png)
                    parts = obj.object_name.split("/")
                    if len(parts) >= 2:
                        try:
                            doc_id = int(parts[1])
                            if doc_id not in valid_document_ids:
                                orphaned.append({
                                    "object_name": obj.object_name,
                                    "size": obj.size or 0,
                                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                                })
                        except (ValueError, IndexError):
                            continue

            return orphaned
        except S3Error:
            return []

    def cleanup_orphaned_files(
        self,
        valid_document_ids: set,
        bucket_name: str = None,
    ) -> dict:
        """
        고아 파일 정리

        Args:
            valid_document_ids: 유효한 문서 ID 집합
            bucket_name: 버킷 이름

        Returns:
            정리 결과
        """
        bucket = bucket_name or settings.MINIO_BUCKET
        deleted_count = 0
        deleted_size = 0
        errors = []

        try:
            orphaned = self.get_orphaned_files(valid_document_ids, bucket)

            for file_info in orphaned:
                try:
                    self.client.remove_object(bucket, file_info["object_name"])
                    deleted_count += 1
                    deleted_size += file_info["size"]
                except S3Error as e:
                    errors.append({
                        "object_name": file_info["object_name"],
                        "error": str(e),
                    })

            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "errors": errors,
            }
        except S3Error as e:
            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "errors": [{"error": str(e)}],
            }


# 싱글톤 인스턴스
storage_service = StorageService()
