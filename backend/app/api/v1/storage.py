"""
스토리지 관리 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.document import Document
from app.schemas.storage import (
    StorageStatsResponse,
    OrphanedFilesResponse,
    OrphanedFile,
    CleanupResponse,
    CleanupError,
)
from app.services.storage_service import storage_service


router = APIRouter()


@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats():
    """
    스토리지 통계 조회

    - 전체 사용량
    - 카테고리별 (documents, pages, thumbnails) 사용량
    """
    stats = storage_service.get_storage_stats()
    return StorageStatsResponse(
        bucket_name=stats["bucket_name"],
        total_size_bytes=stats["total_size_bytes"],
        total_objects=stats["total_objects"],
        categories=stats["categories"],
        error=stats.get("error"),
    )


@router.get("/orphaned", response_model=OrphanedFilesResponse)
async def get_orphaned_files(db: Session = Depends(get_db)):
    """
    고아 파일 목록 조회

    DB에 등록되지 않은 문서의 파일들을 찾습니다.
    """
    # DB에서 유효한 문서 ID 조회
    result = db.execute(select(Document.id))
    valid_ids = {row[0] for row in result.fetchall()}

    # 고아 파일 조회
    orphaned = storage_service.get_orphaned_files(valid_ids)

    total_size = sum(f["size"] for f in orphaned)

    return OrphanedFilesResponse(
        count=len(orphaned),
        total_size_bytes=total_size,
        files=[
            OrphanedFile(
                object_name=f["object_name"],
                size=f["size"],
                last_modified=f["last_modified"],
            )
            for f in orphaned
        ],
    )


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_orphaned_files(db: Session = Depends(get_db)):
    """
    고아 파일 정리

    DB에 등록되지 않은 문서의 파일들을 삭제합니다.
    """
    # DB에서 유효한 문서 ID 조회
    result = db.execute(select(Document.id))
    valid_ids = {row[0] for row in result.fetchall()}

    # 고아 파일 정리
    cleanup_result = storage_service.cleanup_orphaned_files(valid_ids)

    return CleanupResponse(
        deleted_count=cleanup_result["deleted_count"],
        deleted_size_bytes=cleanup_result["deleted_size_bytes"],
        errors=[
            CleanupError(
                object_name=e.get("object_name"),
                error=e["error"],
            )
            for e in cleanup_result["errors"]
        ],
    )
