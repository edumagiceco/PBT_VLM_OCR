from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.document import OCRMode, DocumentStatus, Importance, BlockType


class BlockBase(BaseModel):
    block_type: BlockType = BlockType.TEXT
    bbox: Optional[List[float]] = None
    text: Optional[str] = None
    table_json: Optional[dict] = None


class BlockResponse(BlockBase):
    id: int
    page_id: int
    block_order: int
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlockUpdate(BaseModel):
    text: Optional[str] = None
    table_json: Optional[dict] = None


class PageBase(BaseModel):
    page_no: int
    width: Optional[int] = None
    height: Optional[int] = None


class PageResponse(PageBase):
    id: int
    document_id: int
    image_path: Optional[str] = None
    ocr_json: Optional[dict] = None
    raw_text: Optional[str] = None
    layout_score: Optional[float] = None
    confidence: Optional[float] = None
    blocks: List[BlockResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str
    department: Optional[str] = None
    doc_type: Optional[str] = None
    importance: Importance = Importance.MEDIUM
    ocr_mode: OCRMode = OCRMode.AUTO


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    doc_type: Optional[str] = None
    importance: Optional[Importance] = None
    ocr_mode: Optional[OCRMode] = None


class DocumentResponse(DocumentBase):
    id: int
    original_filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    page_count: int = 0
    recommended_ocr_mode: Optional[OCRMode] = None
    precision_score: Optional[int] = None
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    pages: List[PageResponse] = []

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[DocumentResponse]


class OCRModeRecommendation(BaseModel):
    recommended_mode: OCRMode
    precision_score: int
    reasons: List[str]
