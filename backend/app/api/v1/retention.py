"""
문서 보관 정책 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.retention_service import retention_service


router = APIRouter()


class RetentionSettingsResponse(BaseModel):
    """보관 정책 설정 응답"""
    enabled: bool
    days: int
    min_documents: int
    delete_files: bool
    auto_run_hour: int


class DocumentPreview(BaseModel):
    """문서 미리보기"""
    id: int
    filename: str
    created_at: str
    file_size: Optional[int] = None


class CleanupPreviewResponse(BaseModel):
    """정리 미리보기 응답"""
    count: int
    total_size_bytes: int
    oldest_date: Optional[str] = None
    newest_date: Optional[str] = None
    retention_days: int
    min_documents: int
    delete_files: bool
    documents: List[DocumentPreview]


class CleanupError(BaseModel):
    """정리 오류"""
    document_id: int
    filename: str
    error: str


class CleanupResponse(BaseModel):
    """정리 실행 응답"""
    deleted_count: int
    deleted_size_bytes: int
    remaining_documents: int
    errors: List[CleanupError]


@router.get("/settings", response_model=RetentionSettingsResponse)
async def get_retention_settings(db: Session = Depends(get_db)):
    """
    현재 보관 정책 설정 조회
    """
    settings = retention_service.get_retention_settings(db)
    return RetentionSettingsResponse(**settings)


@router.get("/preview", response_model=CleanupPreviewResponse)
async def preview_cleanup(db: Session = Depends(get_db)):
    """
    정리 대상 문서 미리보기

    실제로 삭제하지 않고 삭제될 문서 목록을 반환합니다.
    """
    preview = retention_service.preview_cleanup(db)
    return CleanupPreviewResponse(
        count=preview["count"],
        total_size_bytes=preview["total_size_bytes"],
        oldest_date=preview["oldest_date"],
        newest_date=preview["newest_date"],
        retention_days=preview["retention_days"],
        min_documents=preview["min_documents"],
        delete_files=preview["delete_files"],
        documents=[
            DocumentPreview(
                id=d["id"],
                filename=d["filename"],
                created_at=d["created_at"],
                file_size=d["file_size"],
            )
            for d in preview["documents"]
        ],
    )


@router.post("/execute", response_model=CleanupResponse)
async def execute_cleanup(db: Session = Depends(get_db)):
    """
    문서 정리 실행

    보관 정책에 따라 오래된 문서를 삭제합니다.
    """
    settings = retention_service.get_retention_settings(db)
    result = retention_service.execute_cleanup(
        db,
        delete_files=settings["delete_files"],
    )
    return CleanupResponse(
        deleted_count=result["deleted_count"],
        deleted_size_bytes=result["deleted_size_bytes"],
        remaining_documents=result["remaining_documents"],
        errors=[
            CleanupError(
                document_id=e["document_id"],
                filename=e["filename"],
                error=e["error"],
            )
            for e in result["errors"]
        ],
    )
