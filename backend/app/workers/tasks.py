"""
OCR 처리 Celery 태스크

VLM OCR: https://github.com/datalab-to/chandra
"""
import os
from datetime import datetime
from typing import Optional, List

from celery import shared_task
from sqlalchemy.orm import Session
from PIL import Image
from pdf2image import convert_from_path
import tempfile

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import (
    Document,
    DocumentPage,
    DocumentBlock,
    DocumentStatus,
    OCRMode,
    BlockType,
)
from app.services.storage_service import storage_service


@celery_app.task(bind=True, name="process_document")
def process_document(self, document_id: int):
    """문서 OCR 처리 메인 태스크"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"status": "error", "message": "Document not found"}

        document.status = DocumentStatus.PROCESSING
        db.commit()

        # OCR 모드 결정
        ocr_mode = document.ocr_mode
        if ocr_mode == OCRMode.AUTO:
            ocr_mode = _determine_ocr_mode(document)
            document.recommended_ocr_mode = ocr_mode

        # OCR 처리 (3가지 모드)
        if ocr_mode == OCRMode.FAST:
            _process_fast_ocr(db, document)
        elif ocr_mode == OCRMode.ACCURATE:
            _process_accurate_ocr(db, document)
        else:  # PRECISION
            _process_precision_ocr(db, document)

        document.status = DocumentStatus.COMPLETED
        document.processed_at = datetime.utcnow()
        db.commit()

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        db.commit()
        raise

    finally:
        db.close()


def _determine_ocr_mode(document: Document) -> OCRMode:
    """OCR 모드 자동 결정"""
    from app.services.ocr_service import recommend_ocr_mode
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        recommendation = loop.run_until_complete(recommend_ocr_mode(document))
        return recommendation.recommended_mode
    finally:
        loop.close()


def _load_document_images(document: Document, tmpdir: str) -> List[Image.Image]:
    """문서 파일을 이미지로 로드"""
    # MinIO에서 파일 다운로드
    local_file = os.path.join(tmpdir, "document")
    storage_service.download_to_file(document.file_path, local_file)

    # 파일 형식에 따라 처리
    if document.mime_type == "application/pdf":
        images = convert_from_path(local_file, dpi=200)
    else:
        images = [Image.open(local_file)]
        # RGB로 변환
        images = [img.convert("RGB") if img.mode != "RGB" else img for img in images]

    return images


def _save_page_images(
    document: Document,
    images: List[Image.Image],
    save_thumbnails: bool = True,
) -> List[str]:
    """
    페이지 이미지를 MinIO에 저장

    Args:
        document: 문서 객체
        images: PIL 이미지 리스트
        save_thumbnails: 썸네일 저장 여부

    Returns:
        저장된 이미지 경로 리스트
    """
    image_paths = []

    for page_no, image in enumerate(images, start=1):
        # 페이지 이미지 저장
        image_path = storage_service.upload_page_image(
            image=image,
            document_id=document.id,
            page_no=page_no,
            format="PNG",
        )
        image_paths.append(image_path)

        # 썸네일 저장
        if save_thumbnails:
            storage_service.upload_thumbnail(
                image=image,
                document_id=document.id,
                page_no=page_no,
            )

    return image_paths


def _process_fast_ocr(db: Session, document: Document):
    """
    빠른 OCR 처리 (Tesseract)
    CPU 기반, 가장 빠른 처리 속도
    """
    import pytesseract

    with tempfile.TemporaryDirectory() as tmpdir:
        # 문서 이미지 로드
        images = _load_document_images(document, tmpdir)
        document.page_count = len(images)

        # 페이지 이미지 저장
        image_paths = _save_page_images(document, images)

        for page_no, (image, image_path) in enumerate(zip(images, image_paths), start=1):
            # Tesseract OCR 실행
            ocr_data = pytesseract.image_to_data(
                image, lang="kor+eng", output_type=pytesseract.Output.DICT
            )
            raw_text = pytesseract.image_to_string(image, lang="kor+eng")

            # 페이지 저장
            width, height = image.size
            page = DocumentPage(
                document_id=document.id,
                page_no=page_no,
                image_path=image_path,
                width=width,
                height=height,
                raw_text=raw_text,
                ocr_json={"tesseract_data": ocr_data, "ocr_engine": "tesseract"},
                confidence=_calculate_confidence(ocr_data),
            )
            db.add(page)
            db.flush()

            # 블록 추출 및 저장
            blocks = _extract_blocks_from_tesseract(ocr_data, width, height)
            for block_order, block_data in enumerate(blocks):
                block = DocumentBlock(
                    page_id=page.id,
                    block_order=block_order,
                    block_type=BlockType.TEXT,
                    bbox=block_data["bbox"],
                    text=block_data["text"],
                    confidence=block_data["confidence"],
                )
                db.add(block)

        db.commit()


def _process_accurate_ocr(db: Session, document: Document):
    """
    정확 OCR 처리 (PaddleOCR)
    딥러닝 기반, 높은 정확도

    https://github.com/PaddlePaddle/PaddleOCR
    """
    # PaddleOCR 프로세서 임포트 시도
    paddle_available = False
    try:
        from workers.accurate_ocr.processor import PaddleOCRProcessor
        paddle_available = True
    except ImportError:
        try:
            import sys
            sys.path.insert(0, "/app/workers/accurate_ocr")
            from processor import PaddleOCRProcessor
            paddle_available = True
        except ImportError:
            pass

    # PaddleOCR가 없으면 빠른 OCR로 대체
    if not paddle_available:
        print(f"[INFO] PaddleOCR not available, falling back to fast OCR for document {document.id}")
        _process_fast_ocr(db, document)
        return

    # PaddleOCR 프로세서 초기화
    processor = PaddleOCRProcessor(
        use_gpu=False,  # CPU 모드
        lang="korean",
        dpi=200,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # MinIO에서 파일 다운로드
        local_file = os.path.join(tmpdir, "document")
        storage_service.download_to_file(document.file_path, local_file)

        # 이미지 로드 (썸네일용)
        if document.mime_type == "application/pdf":
            preview_images = convert_from_path(local_file, dpi=200)
        else:
            preview_images = [Image.open(local_file)]

        # 페이지 이미지/썸네일 저장
        image_paths = _save_page_images(document, preview_images)

        # PaddleOCR 처리
        if document.mime_type == "application/pdf":
            results = processor.process_pdf(local_file)
        else:
            result = processor.process_image(local_file)
            results = [result]

        document.page_count = len(results)

        for result, image_path in zip(results, image_paths):
            # 페이지 저장
            page = DocumentPage(
                document_id=document.id,
                page_no=result.page_no,
                image_path=image_path,
                width=result.width,
                height=result.height,
                raw_text=result.raw_text,
                ocr_json={
                    "markdown": result.markdown,
                    "html": result.html,
                    "ocr_engine": "paddleocr",
                    "blocks": [
                        {
                            "type": b.block_type,
                            "text": b.text,
                            "bbox": b.bbox,
                            "confidence": b.confidence,
                            "reading_order": b.reading_order,
                        }
                        for b in result.blocks
                    ],
                },
                layout_score=result.layout_score,
                confidence=result.confidence,
            )
            db.add(page)
            db.flush()

            # 블록 저장
            for block_data in result.blocks:
                block_type = _map_block_type(block_data.block_type)

                block = DocumentBlock(
                    page_id=page.id,
                    block_order=block_data.reading_order,
                    block_type=block_type,
                    bbox=block_data.bbox,
                    text=block_data.text,
                    confidence=block_data.confidence,
                )
                db.add(block)

        db.commit()


def _process_precision_ocr(db: Session, document: Document):
    """
    정밀 OCR 처리 (Chandra VLM)
    GPU 기반

    https://github.com/datalab-to/chandra

    GPU/VLM이 없는 환경에서는 일반 OCR로 대체
    """
    # VLM 서버 확인
    vllm_api_base = os.getenv("VLLM_API_BASE", "")

    # Chandra 프로세서 임포트 시도
    chandra_available = False
    if vllm_api_base:
        try:
            from workers.precision_ocr.processor import ChandraOCRProcessor
            chandra_available = True
        except ImportError:
            try:
                import sys
                sys.path.insert(0, "/app/workers/precision_ocr")
                from processor import ChandraOCRProcessor
                chandra_available = True
            except ImportError:
                pass

    # Chandra가 없으면 빠른 OCR로 대체
    if not chandra_available:
        print(f"[INFO] Precision OCR not available, falling back to fast OCR for document {document.id}")
        _process_fast_ocr(db, document)
        return

    # Chandra 프로세서 초기화
    # DPI 150 사용 (이미지 토큰이 모델 컨텍스트 제한 4096을 초과하지 않도록)
    processor = ChandraOCRProcessor(
        api_base=vllm_api_base,
        dpi=150,  # 300에서 150으로 감소
        max_tokens=2048,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # MinIO에서 파일 다운로드
        local_file = os.path.join(tmpdir, "document")
        storage_service.download_to_file(document.file_path, local_file)

        # 저해상도 이미지 로드 (썸네일용)
        if document.mime_type == "application/pdf":
            preview_images = convert_from_path(local_file, dpi=150)
        else:
            preview_images = [Image.open(local_file)]

        # 페이지 이미지/썸네일 저장
        image_paths = _save_page_images(document, preview_images)

        # Chandra OCR 처리 (고해상도)
        if document.mime_type == "application/pdf":
            results = processor.process_pdf(local_file)
        else:
            result = processor.process_image(local_file)
            results = [result]

        document.page_count = len(results)

        for result, image_path in zip(results, image_paths):
            # 페이지 저장
            page = DocumentPage(
                document_id=document.id,
                page_no=result.page_no,
                image_path=image_path,
                width=result.width,
                height=result.height,
                raw_text=result.raw_text,
                ocr_json={
                    "markdown": result.markdown,
                    "html": result.html,
                    "blocks": [
                        {
                            "type": b.block_type,
                            "text": b.text,
                            "bbox": b.bbox,
                            "confidence": b.confidence,
                            "reading_order": b.reading_order,
                            "table": b.table.__dict__ if b.table else None,
                        }
                        for b in result.blocks
                    ],
                },
                layout_score=result.layout_score,
                confidence=result.confidence,
            )
            db.add(page)
            db.flush()

            # 블록 저장
            for block_data in result.blocks:
                block_type = _map_block_type(block_data.block_type)
                table_json = None
                if block_data.table:
                    table_json = {"rows": block_data.table.rows}

                block = DocumentBlock(
                    page_id=page.id,
                    block_order=block_data.reading_order,
                    block_type=block_type,
                    bbox=block_data.bbox,
                    text=block_data.text,
                    table_json=table_json,
                    confidence=block_data.confidence,
                )
                db.add(block)

        db.commit()


def _calculate_confidence(ocr_data: dict) -> float:
    """Tesseract 결과에서 평균 confidence 계산"""
    confidences = [
        float(c) for c in ocr_data.get("conf", [])
        if c != "-1" and str(c).isdigit()
    ]
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences) / 100.0


def _extract_blocks_from_tesseract(
    ocr_data: dict, page_width: int, page_height: int
) -> list:
    """Tesseract 결과에서 블록 추출"""
    blocks = []
    current_block_num = -1
    current_block = {"texts": [], "bbox": None, "confidences": []}

    n_boxes = len(ocr_data.get("text", []))
    for i in range(n_boxes):
        text = ocr_data["text"][i].strip()
        block_num = ocr_data["block_num"][i]
        conf = float(ocr_data["conf"][i]) if ocr_data["conf"][i] != "-1" else 0

        if block_num != current_block_num:
            # 이전 블록 저장
            if current_block["texts"] and current_block["bbox"]:
                blocks.append({
                    "text": " ".join(current_block["texts"]),
                    "bbox": current_block["bbox"],
                    "confidence": (
                        sum(current_block["confidences"]) /
                        len(current_block["confidences"]) / 100.0
                        if current_block["confidences"] else 0.0
                    ),
                })
            current_block = {"texts": [], "bbox": None, "confidences": []}
            current_block_num = block_num

        if text and conf > 0:
            current_block["texts"].append(text)
            current_block["confidences"].append(conf)

            x, y, w, h = (
                ocr_data["left"][i],
                ocr_data["top"][i],
                ocr_data["width"][i],
                ocr_data["height"][i],
            )
            bbox = [
                x / page_width,
                y / page_height,
                (x + w) / page_width,
                (y + h) / page_height,
            ]

            if current_block["bbox"] is None:
                current_block["bbox"] = bbox
            else:
                current_block["bbox"] = [
                    min(current_block["bbox"][0], bbox[0]),
                    min(current_block["bbox"][1], bbox[1]),
                    max(current_block["bbox"][2], bbox[2]),
                    max(current_block["bbox"][3], bbox[3]),
                ]

    # 마지막 블록 저장
    if current_block["texts"] and current_block["bbox"]:
        blocks.append({
            "text": " ".join(current_block["texts"]),
            "bbox": current_block["bbox"],
            "confidence": (
                sum(current_block["confidences"]) /
                len(current_block["confidences"]) / 100.0
                if current_block["confidences"] else 0.0
            ),
        })

    return blocks


def _map_block_type(block_type_str: str) -> BlockType:
    """문자열 블록 타입을 Enum으로 변환"""
    mapping = {
        "text": BlockType.TEXT,
        "table": BlockType.TABLE,
        "image": BlockType.IMAGE,
        "header": BlockType.HEADER,
        "footer": BlockType.FOOTER,
        "list": BlockType.LIST,
    }
    return mapping.get(block_type_str, BlockType.TEXT)


@celery_app.task(name="generate_embeddings")
def generate_embeddings(document_id: int):
    """문서 임베딩 생성 (Phase 2)"""
    # TODO: 구현
    # 1. 문서 텍스트 청킹
    # 2. 임베딩 모델로 벡터 생성
    # 3. Qdrant에 저장
    pass


@celery_app.task(name="cleanup_document_files")
def cleanup_document_files(document_id: int):
    """문서 관련 파일 정리"""
    storage_service.delete_document_files(document_id)
