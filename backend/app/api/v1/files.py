"""
파일/이미지 관련 API

MinIO presigned URL을 통한 파일 접근 제공
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.storage_service import storage_service
from app.services import document_service

router = APIRouter()


class PresignedUrlResponse(BaseModel):
    url: str
    expires_in: int  # seconds


class PageImageUrls(BaseModel):
    page_no: int
    image_url: str
    thumbnail_url: str


class DocumentImagesResponse(BaseModel):
    document_id: int
    pages: list[PageImageUrls]


@router.get("/documents/{document_id}/file-url", response_model=PresignedUrlResponse)
async def get_document_file_url(
    document_id: int,
    expires_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """
    원본 문서 파일의 presigned URL 생성

    Args:
        document_id: 문서 ID
        expires_minutes: URL 만료 시간 (분, 기본 60분, 최대 24시간)
    """
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    url = storage_service.get_presigned_url(
        document.file_path,
        expires=timedelta(minutes=expires_minutes),
    )

    return PresignedUrlResponse(
        url=url,
        expires_in=expires_minutes * 60,
    )


@router.get("/documents/{document_id}/pages/{page_no}/image-url", response_model=PresignedUrlResponse)
async def get_page_image_url(
    document_id: int,
    page_no: int,
    expires_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """
    페이지 이미지의 presigned URL 생성

    Args:
        document_id: 문서 ID
        page_no: 페이지 번호
        expires_minutes: URL 만료 시간 (분)
    """
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 페이지 확인
    page = next((p for p in document.pages if p.page_no == page_no), None)
    if not page or not page.image_path:
        raise HTTPException(status_code=404, detail="Page image not found")

    url = storage_service.get_presigned_url(
        page.image_path,
        expires=timedelta(minutes=expires_minutes),
    )

    return PresignedUrlResponse(
        url=url,
        expires_in=expires_minutes * 60,
    )


@router.get("/documents/{document_id}/pages/{page_no}/thumbnail-url", response_model=PresignedUrlResponse)
async def get_page_thumbnail_url(
    document_id: int,
    page_no: int,
    expires_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """
    페이지 썸네일의 presigned URL 생성

    Args:
        document_id: 문서 ID
        page_no: 페이지 번호
        expires_minutes: URL 만료 시간 (분)
    """
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 썸네일 경로 생성
    thumbnail_path = f"thumbnails/{document_id}/page_{page_no:04d}.jpg"

    if not storage_service.file_exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    url = storage_service.get_presigned_url(
        thumbnail_path,
        expires=timedelta(minutes=expires_minutes),
    )

    return PresignedUrlResponse(
        url=url,
        expires_in=expires_minutes * 60,
    )


@router.get("/documents/{document_id}/images", response_model=DocumentImagesResponse)
async def get_document_all_image_urls(
    document_id: int,
    expires_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """
    문서의 모든 페이지 이미지 URL 일괄 조회

    Args:
        document_id: 문서 ID
        expires_minutes: URL 만료 시간 (분)
    """
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = []
    for page in sorted(document.pages, key=lambda p: p.page_no):
        image_url = ""
        thumbnail_url = ""

        if page.image_path:
            image_url = storage_service.get_presigned_url(
                page.image_path,
                expires=timedelta(minutes=expires_minutes),
            )

        thumbnail_path = f"thumbnails/{document_id}/page_{page.page_no:04d}.jpg"
        if storage_service.file_exists(thumbnail_path):
            thumbnail_url = storage_service.get_presigned_url(
                thumbnail_path,
                expires=timedelta(minutes=expires_minutes),
            )

        pages.append(PageImageUrls(
            page_no=page.page_no,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
        ))

    return DocumentImagesResponse(
        document_id=document_id,
        pages=pages,
    )


@router.get("/documents/{document_id}/pages/{page_no}/image")
async def get_page_image(
    document_id: int,
    page_no: int,
    db: Session = Depends(get_db),
):
    """
    페이지 이미지 직접 반환 (프록시)

    Args:
        document_id: 문서 ID
        page_no: 페이지 번호
    """
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 페이지 확인
    page = next((p for p in document.pages if p.page_no == page_no), None)
    if not page or not page.image_path:
        raise HTTPException(status_code=404, detail="Page image not found")

    try:
        image_data = storage_service.download_file(page.image_path)
        # 확장자에 따라 content type 결정
        content_type = "image/png"
        if page.image_path.endswith(".jpg") or page.image_path.endswith(".jpeg"):
            content_type = "image/jpeg"
        return Response(content=image_data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")


@router.get("/documents/{document_id}/pages/{page_no}/thumbnail")
async def get_page_thumbnail(
    document_id: int,
    page_no: int,
    db: Session = Depends(get_db),
):
    """
    페이지 썸네일 직접 반환 (프록시)

    Args:
        document_id: 문서 ID
        page_no: 페이지 번호
    """
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 썸네일 경로
    thumbnail_path = f"thumbnails/{document_id}/page_{page_no:04d}.jpg"

    if not storage_service.file_exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    try:
        image_data = storage_service.download_file(thumbnail_path)
        return Response(content=image_data, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch thumbnail: {str(e)}")
