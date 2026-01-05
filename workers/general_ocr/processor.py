"""
일반 OCR 처리기 - CPU 기반 (Tesseract / PaddleOCR)
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

import pytesseract
from PIL import Image
from pdf2image import convert_from_path


@dataclass
class OCRBlock:
    text: str
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    block_type: str = "text"


@dataclass
class PageOCRResult:
    page_no: int
    width: int
    height: int
    blocks: List[OCRBlock]
    raw_text: str
    confidence: float


class GeneralOCRProcessor:
    """일반 OCR 프로세서 (Tesseract 기반)"""

    def __init__(self, lang: str = "kor+eng", dpi: int = 200):
        self.lang = lang
        self.dpi = dpi

    def process_pdf(self, pdf_path: str) -> List[PageOCRResult]:
        """PDF 파일 OCR 처리"""
        images = convert_from_path(pdf_path, dpi=self.dpi)
        results = []

        for page_no, image in enumerate(images, start=1):
            result = self._process_image(image, page_no)
            results.append(result)

        return results

    def process_image(self, image_path: str) -> PageOCRResult:
        """이미지 파일 OCR 처리"""
        image = Image.open(image_path)
        return self._process_image(image, page_no=1)

    def _process_image(self, image: Image.Image, page_no: int) -> PageOCRResult:
        """이미지 OCR 처리"""
        width, height = image.size

        # Tesseract OCR 실행
        data = pytesseract.image_to_data(
            image, lang=self.lang, output_type=pytesseract.Output.DICT
        )

        # 블록 추출
        blocks = self._extract_blocks(data, width, height)

        # 전체 텍스트
        raw_text = pytesseract.image_to_string(image, lang=self.lang)

        # 평균 confidence 계산
        confidences = [b.confidence for b in blocks if b.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return PageOCRResult(
            page_no=page_no,
            width=width,
            height=height,
            blocks=blocks,
            raw_text=raw_text,
            confidence=avg_confidence,
        )

    def _extract_blocks(
        self, data: Dict[str, Any], page_width: int, page_height: int
    ) -> List[OCRBlock]:
        """Tesseract 결과에서 블록 추출"""
        blocks = []
        n_boxes = len(data["text"])

        current_block_texts = []
        current_block_num = -1
        current_bbox = None

        for i in range(n_boxes):
            text = data["text"][i].strip()
            block_num = data["block_num"][i]
            conf = float(data["conf"][i])

            if block_num != current_block_num:
                # 이전 블록 저장
                if current_block_texts and current_bbox:
                    blocks.append(
                        OCRBlock(
                            text=" ".join(current_block_texts),
                            bbox=current_bbox,
                            confidence=conf,
                            block_type="text",
                        )
                    )
                current_block_texts = []
                current_block_num = block_num
                current_bbox = None

            if text and conf > 0:
                current_block_texts.append(text)

                x, y, w, h = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )
                bbox = [
                    x / page_width,
                    y / page_height,
                    (x + w) / page_width,
                    (y + h) / page_height,
                ]

                if current_bbox is None:
                    current_bbox = bbox
                else:
                    # 박스 확장
                    current_bbox = [
                        min(current_bbox[0], bbox[0]),
                        min(current_bbox[1], bbox[1]),
                        max(current_bbox[2], bbox[2]),
                        max(current_bbox[3], bbox[3]),
                    ]

        # 마지막 블록 저장
        if current_block_texts and current_bbox:
            blocks.append(
                OCRBlock(
                    text=" ".join(current_block_texts),
                    bbox=current_bbox,
                    confidence=conf if conf > 0 else 0,
                    block_type="text",
                )
            )

        return blocks


class PaddleOCRProcessor:
    """PaddleOCR 기반 프로세서 (대안)"""

    def __init__(self, lang: str = "korean", dpi: int = 200):
        self.lang = lang
        self.dpi = dpi
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=True, lang=self.lang)
        return self._ocr

    def process_image(self, image_path: str) -> PageOCRResult:
        """이미지 OCR 처리"""
        image = Image.open(image_path)
        width, height = image.size

        result = self.ocr.ocr(image_path, cls=True)
        blocks = []

        for line in result[0]:
            bbox_points, (text, confidence) = line
            # bbox_points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bbox = [
                min(x_coords) / width,
                min(y_coords) / height,
                max(x_coords) / width,
                max(y_coords) / height,
            ]
            blocks.append(
                OCRBlock(text=text, bbox=bbox, confidence=confidence, block_type="text")
            )

        raw_text = "\n".join([b.text for b in blocks])
        avg_confidence = sum(b.confidence for b in blocks) / len(blocks) if blocks else 0

        return PageOCRResult(
            page_no=1,
            width=width,
            height=height,
            blocks=blocks,
            raw_text=raw_text,
            confidence=avg_confidence,
        )
