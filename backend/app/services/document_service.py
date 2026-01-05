"""
문서 관리 서비스

문서 CRUD, OCR 처리 요청 등
"""
import os
import uuid
from typing import Optional
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentBlock, DocumentPage, DocumentStatus, OCRMode
from app.schemas.document import DocumentCreate, DocumentUpdate, BlockUpdate, DocumentListResponse
from app.services.storage_service import storage_service


def _get_ocr_queue(ocr_mode: OCRMode) -> str:
    """OCR 모드에 따른 Celery 큐 선택"""
    queue_mapping = {
        OCRMode.FAST: "fast_ocr",
        OCRMode.ACCURATE: "accurate_ocr",
        OCRMode.PRECISION: "precision_ocr",
        OCRMode.AUTO: "fast_ocr",  # AUTO는 기본적으로 fast 큐로, 태스크에서 재결정
    }
    return queue_mapping.get(ocr_mode, "fast_ocr")


async def create_document(
    db: Session, file: UploadFile, doc_create: DocumentCreate
) -> Document:
    """
    문서 생성 및 저장

    1. MinIO에 원본 파일 저장
    2. DB에 문서 메타데이터 저장
    3. OCR 처리 태스크 호출
    """
    # 파일 데이터 읽기
    file_content = await file.read()

    # MinIO에 파일 업로드
    file_path, file_size = storage_service.upload_document(
        file_data=file_content,
        original_filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
    )

    # DB에 문서 저장
    document = Document(
        title=doc_create.title,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        department=doc_create.department,
        doc_type=doc_create.doc_type,
        importance=doc_create.importance,
        ocr_mode=doc_create.ocr_mode,
        status=DocumentStatus.PENDING,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Celery OCR 태스크 호출 (OCR 모드에 따라 큐 선택)
    from app.workers.tasks import process_document
    queue = _get_ocr_queue(doc_create.ocr_mode)
    process_document.apply_async(args=[document.id], queue=queue)

    return document


async def get_document(db: Session, document_id: int) -> Optional[Document]:
    """문서 조회"""
    return db.query(Document).filter(Document.id == document_id).first()


async def list_documents(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    importance: Optional[str] = None,
) -> DocumentListResponse:
    """문서 목록 조회"""
    query = db.query(Document)

    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))
    if department:
        query = query.filter(Document.department == department)
    if status:
        query = query.filter(Document.status == status)
    if importance:
        query = query.filter(Document.importance == importance)

    total = query.count()
    items = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


async def update_document(
    db: Session, document_id: int, update_data: DocumentUpdate
) -> Optional[Document]:
    """문서 수정"""
    document = await get_document(db, document_id)
    if not document:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(document, key, value)

    db.commit()
    db.refresh(document)
    return document


async def delete_document(db: Session, document_id: int) -> bool:
    """
    문서 삭제

    1. MinIO에서 원본 파일 삭제
    2. MinIO에서 페이지 이미지/썸네일 삭제
    3. DB에서 문서 삭제 (cascade로 페이지/블록도 삭제)
    """
    document = await get_document(db, document_id)
    if not document:
        return False

    # MinIO에서 원본 파일 삭제
    storage_service.delete_file(document.file_path)

    # MinIO에서 페이지 이미지/썸네일 삭제
    storage_service.delete_document_files(document_id)

    # DB에서 삭제
    db.delete(document)
    db.commit()
    return True


async def reprocess_document(
    db: Session, document_id: int, ocr_mode: Optional[OCRMode] = None
) -> Optional[Document]:
    """
    OCR 재처리

    1. 기존 페이지/블록 데이터 삭제
    2. 기존 이미지/썸네일 삭제
    3. 새로운 OCR 태스크 시작
    """
    document = await get_document(db, document_id)
    if not document:
        return None

    # 기존 페이지 및 블록 삭제
    for page in document.pages:
        for block in page.blocks:
            db.delete(block)
        db.delete(page)

    # MinIO에서 기존 이미지 삭제
    storage_service.delete_document_files(document_id)

    if ocr_mode:
        document.ocr_mode = ocr_mode

    document.status = DocumentStatus.PENDING
    document.error_message = None
    document.processed_at = None
    document.page_count = 0
    db.commit()

    # Celery 태스크 호출 (OCR 모드에 따라 큐 선택)
    from app.workers.tasks import process_document
    queue = _get_ocr_queue(document.ocr_mode)
    process_document.apply_async(args=[document.id], queue=queue)

    db.refresh(document)
    return document


async def update_block(
    db: Session, document_id: int, block_id: int, update_data: BlockUpdate
) -> Optional[DocumentBlock]:
    """블록 수정 (검수)"""
    block = (
        db.query(DocumentBlock)
        .join(DocumentBlock.page)
        .filter(
            DocumentBlock.id == block_id,
            DocumentBlock.page.has(document_id=document_id),
        )
        .first()
    )

    if not block:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(block, key, value)

    db.commit()
    db.refresh(block)
    return block


async def get_document_statistics(db: Session) -> dict:
    """문서 통계 조회"""
    total = db.query(Document).count()
    by_status = {}
    for status in DocumentStatus:
        count = db.query(Document).filter(Document.status == status).count()
        by_status[status.value] = count

    by_ocr_mode = {}
    for mode in OCRMode:
        count = db.query(Document).filter(Document.ocr_mode == mode).count()
        by_ocr_mode[mode.value] = count

    return {
        "total": total,
        "by_status": by_status,
        "by_ocr_mode": by_ocr_mode,
    }
