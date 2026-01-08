from typing import Optional, List
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentUpdate,
    BlockUpdate,
    BlockResponse,
    OCRModeRecommendation,
)
from app.services import document_service, ocr_service, export_service
from app.models.document import OCRMode, Importance, DocumentStatus


class ProcessingQueueItem(BaseModel):
    id: int
    title: str
    original_filename: str
    status: str
    ocr_mode: str
    page_count: int
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ProcessingQueueResponse(BaseModel):
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    items: List[ProcessingQueueItem]

router = APIRouter()


@router.get("/queue", response_model=ProcessingQueueResponse)
async def get_processing_queue(
    db: Session = Depends(get_db),
):
    """OCR 처리 대기열 조회"""
    from app.models.document import Document

    # 상태별 카운트
    pending = db.query(Document).filter(Document.status == DocumentStatus.PENDING).count()
    processing = db.query(Document).filter(Document.status == DocumentStatus.PROCESSING).count()
    completed = db.query(Document).filter(Document.status == DocumentStatus.COMPLETED).count()
    failed = db.query(Document).filter(Document.status == DocumentStatus.FAILED).count()
    total = pending + processing + completed + failed

    # 최근 문서 목록 (처리 중/대기 중 우선, 최근 순)
    items = (
        db.query(Document)
        .order_by(
            # 처리 중 > 대기 중 > 실패 > 완료 순서
            (Document.status == DocumentStatus.PROCESSING).desc(),
            (Document.status == DocumentStatus.PENDING).desc(),
            (Document.status == DocumentStatus.FAILED).desc(),
            Document.updated_at.desc(),
        )
        .limit(50)
        .all()
    )

    return ProcessingQueueResponse(
        total=total,
        pending=pending,
        processing=processing,
        completed=completed,
        failed=failed,
        items=[
            ProcessingQueueItem(
                id=doc.id,
                title=doc.title,
                original_filename=doc.original_filename,
                status=doc.status.value if hasattr(doc.status, 'value') else (doc.status or "pending"),
                ocr_mode=doc.ocr_mode.value if hasattr(doc.ocr_mode, 'value') else (doc.ocr_mode or "auto"),
                page_count=doc.page_count or 0,
                file_size=doc.file_size,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                processed_at=doc.processed_at,
                error_message=doc.error_message,
            )
            for doc in items
        ],
    )


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    doc_type: Optional[str] = Form(None),
    importance: Importance = Form(Importance.MEDIUM),
    ocr_mode: OCRMode = Form(OCRMode.AUTO),
    db: Session = Depends(get_db),
):
    """문서 업로드 및 OCR 처리 시작"""
    if not title:
        title = file.filename

    doc_create = DocumentCreate(
        title=title,
        department=department,
        doc_type=doc_type,
        importance=importance,
        ocr_mode=ocr_mode,
    )

    document = await document_service.create_document(db, file, doc_create)
    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    importance: Optional[Importance] = Query(None),
    db: Session = Depends(get_db),
):
    """문서 목록 조회 및 검색"""
    return await document_service.list_documents(
        db,
        page=page,
        page_size=page_size,
        search=search,
        department=department,
        status=status,
        importance=importance,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """문서 상세 조회"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db),
):
    """문서 정보 수정"""
    document = await document_service.update_document(db, document_id, update_data)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """문서 삭제"""
    success = await document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/recommend-ocr", response_model=OCRModeRecommendation)
async def recommend_ocr_mode(document_id: int, db: Session = Depends(get_db)):
    """OCR 모드 추천"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return await ocr_service.recommend_ocr_mode(document)


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    ocr_mode: Optional[OCRMode] = Query(None),
    db: Session = Depends(get_db),
):
    """OCR 재처리"""
    document = await document_service.reprocess_document(db, document_id, ocr_mode)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.patch("/{document_id}/blocks/{block_id}", response_model=BlockResponse)
async def update_block(
    document_id: int,
    block_id: int,
    update_data: BlockUpdate,
    db: Session = Depends(get_db),
):
    """블록 수정 (검수)"""
    block = await document_service.update_block(db, document_id, block_id, update_data)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return block


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    format: str = Query("md", pattern="^(md|json|html)$"),
    db: Session = Depends(get_db),
):
    """문서 다운로드 (md/json/html)"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    content, content_type, filename = await export_service.export_document(
        document, format
    )

    # RFC 5987 encoding for non-ASCII filenames
    encoded_filename = quote(filename, safe='')

    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
