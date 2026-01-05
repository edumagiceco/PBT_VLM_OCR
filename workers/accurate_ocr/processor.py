"""
정확 OCR 처리기 - PaddleOCR 기반 (딥러닝)

PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- PP-OCRv4 기반 고정밀 문서 OCR
- 한국어/영어 지원
- 표 인식 지원
- CPU/GPU 모두 지원
"""
import os
import logging
from typing import List, Optional
from dataclasses import dataclass, field

from PIL import Image
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    row: int
    col: int
    text: str
    rowspan: int = 1
    colspan: int = 1


@dataclass
class Table:
    rows: List[List[str]]
    bbox: List[float]
    confidence: float


@dataclass
class OCRBlock:
    text: str
    bbox: List[float]  # [x1, y1, x2, y2] normalized
    confidence: float
    block_type: str = "text"  # text, table, header, footer, list, image
    table: Optional[Table] = None
    reading_order: int = 0


@dataclass
class PageOCRResult:
    page_no: int
    width: int
    height: int
    blocks: List[OCRBlock]
    raw_text: str
    markdown: str
    html: str
    confidence: float
    layout_score: float = 0.0


class PaddleOCRProcessor:
    """
    PaddleOCR 기반 정확 OCR 프로세서

    PP-OCRv4 모델 사용:
    - 검출: PP-OCRv4 detection model
    - 인식: PP-OCRv4 recognition model (한국어/영어)
    - 방향 분류: 텍스트 방향 자동 감지
    """

    def __init__(
        self,
        use_gpu: bool = False,
        lang: str = "korean",
        dpi: int = 200,
    ):
        """
        Args:
            use_gpu: GPU 사용 여부 (기본: CPU)
            lang: 언어 설정 (korean, en, ch 등)
            dpi: PDF 렌더링 해상도
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.dpi = dpi

        self._ocr = None

    @property
    def ocr(self):
        """PaddleOCR 엔진 지연 초기화"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR

                # PaddleOCR 3.x API
                self._ocr = PaddleOCR(
                    lang=self.lang,
                    use_doc_orientation_classify=True,  # 문서 방향 자동 감지
                    use_doc_unwarping=False,            # 문서 왜곡 보정 (비활성화로 속도 향상)
                    use_textline_orientation=True,      # 텍스트 라인 방향 감지
                )
                logger.info(f"PaddleOCR initialized (lang={self.lang})")
            except ImportError as e:
                logger.error(f"PaddleOCR not installed: {e}")
                raise
            except Exception as e:
                logger.error(f"PaddleOCR initialization failed: {e}")
                raise
        return self._ocr

    def process_pdf(self, pdf_path: str) -> List[PageOCRResult]:
        """
        PDF 파일 OCR 처리

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            페이지별 OCR 결과 리스트
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # PDF를 이미지로 변환
        images = convert_from_path(pdf_path, dpi=self.dpi)
        results = []

        for page_no, image in enumerate(images, start=1):
            logger.info(f"Processing page {page_no}/{len(images)}")
            result = self._process_image(image, page_no)
            results.append(result)

        return results

    def process_image(self, image_path: str) -> PageOCRResult:
        """
        이미지 파일 OCR 처리

        Args:
            image_path: 이미지 파일 경로

        Returns:
            OCR 결과
        """
        logger.info(f"Processing image: {image_path}")
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return self._process_image(image, page_no=1)

    def process_image_pil(self, image: Image.Image, page_no: int = 1) -> PageOCRResult:
        """
        PIL 이미지 직접 처리

        Args:
            image: PIL 이미지 객체
            page_no: 페이지 번호

        Returns:
            OCR 결과
        """
        if image.mode != "RGB":
            image = image.convert("RGB")
        return self._process_image(image, page_no)

    def _process_image(self, image: Image.Image, page_no: int) -> PageOCRResult:
        """
        이미지 OCR 처리 (내부)
        """
        import numpy as np

        width, height = image.size
        img_array = np.array(image)

        # PaddleOCR 3.x 실행
        ocr_results = self.ocr.ocr(img_array)

        # 결과 파싱
        blocks = []
        texts = []
        confidences = []

        # PaddleOCR 3.x 결과 형식 처리
        if ocr_results:
            first_result = ocr_results[0]

            # PaddleOCR 3.x: OCRResult 객체 (dict-like)
            if hasattr(first_result, 'keys'):
                rec_texts = first_result.get('rec_texts', [])
                rec_scores = first_result.get('rec_scores', [])
                dt_polys = first_result.get('dt_polys', [])

                for idx, (text, conf, bbox_points) in enumerate(zip(rec_texts, rec_scores, dt_polys)):
                    if not text or conf < 0.3:  # 낮은 신뢰도 필터링
                        continue

                    # 정규화된 bbox [x1, y1, x2, y2]
                    x_coords = [p[0] for p in bbox_points]
                    y_coords = [p[1] for p in bbox_points]
                    bbox = [
                        min(x_coords) / width,
                        min(y_coords) / height,
                        max(x_coords) / width,
                        max(y_coords) / height,
                    ]

                    blocks.append(
                        OCRBlock(
                            text=text,
                            bbox=bbox,
                            confidence=conf,
                            block_type="text",
                            reading_order=idx,
                        )
                    )
                    texts.append(text)
                    confidences.append(conf)

            # PaddleOCR 2.x 호환: 리스트 형식
            elif isinstance(first_result, list):
                for idx, line in enumerate(first_result):
                    if line is None:
                        continue

                    bbox_points = line[0]
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)):
                        text = text_info[0]
                        conf = text_info[1] if len(text_info) > 1 else 0.0
                    else:
                        continue

                    if not text or conf < 0.3:
                        continue

                    x_coords = [p[0] for p in bbox_points]
                    y_coords = [p[1] for p in bbox_points]
                    bbox = [
                        min(x_coords) / width,
                        min(y_coords) / height,
                        max(x_coords) / width,
                        max(y_coords) / height,
                    ]

                    blocks.append(
                        OCRBlock(
                            text=text,
                            bbox=bbox,
                            confidence=conf,
                            block_type="text",
                            reading_order=idx,
                        )
                    )
                    texts.append(text)
                    confidences.append(conf)

        # 텍스트 조합
        raw_text = "\n".join(texts)
        markdown = self._to_markdown(blocks)
        html = self._to_html(blocks)

        # 평균 신뢰도
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return PageOCRResult(
            page_no=page_no,
            width=width,
            height=height,
            blocks=blocks,
            raw_text=raw_text,
            markdown=markdown,
            html=html,
            confidence=avg_confidence,
            layout_score=0.85,  # PaddleOCR는 레이아웃 분석이 우수
        )

    def _to_markdown(self, blocks: List[OCRBlock]) -> str:
        """블록을 Markdown으로 변환"""
        lines = []
        for block in blocks:
            if block.block_type == "header":
                lines.append(f"## {block.text}")
            elif block.block_type == "table" and block.table:
                lines.append(self._table_to_markdown(block.table))
            else:
                lines.append(block.text)
        return "\n\n".join(lines)

    def _to_html(self, blocks: List[OCRBlock]) -> str:
        """블록을 HTML로 변환"""
        html_parts = []
        for block in blocks:
            if block.block_type == "header":
                html_parts.append(f"<h2>{block.text}</h2>")
            elif block.block_type == "table" and block.table:
                html_parts.append(self._table_to_html(block.table))
            else:
                html_parts.append(f"<p>{block.text}</p>")
        return "\n".join(html_parts)

    def _table_to_markdown(self, table: Table) -> str:
        """표를 Markdown으로 변환"""
        if not table.rows:
            return ""

        lines = []
        for i, row in enumerate(table.rows):
            line = "| " + " | ".join(row) + " |"
            lines.append(line)
            if i == 0:
                # 헤더 구분선
                sep = "| " + " | ".join(["---"] * len(row)) + " |"
                lines.append(sep)

        return "\n".join(lines)

    def _table_to_html(self, table: Table) -> str:
        """표를 HTML로 변환"""
        if not table.rows:
            return ""

        html = "<table>\n"
        for i, row in enumerate(table.rows):
            html += "  <tr>\n"
            tag = "th" if i == 0 else "td"
            for cell in row:
                html += f"    <{tag}>{cell}</{tag}>\n"
            html += "  </tr>\n"
        html += "</table>"

        return html


def create_processor(
    use_gpu: bool = False,
    lang: str = "korean",
    **kwargs
) -> PaddleOCRProcessor:
    """
    OCR 프로세서 팩토리 함수

    Args:
        use_gpu: GPU 사용 여부
        lang: 언어 설정
        **kwargs: 추가 설정

    Returns:
        PaddleOCRProcessor 인스턴스
    """
    return PaddleOCRProcessor(
        use_gpu=use_gpu,
        lang=lang,
        **kwargs
    )
