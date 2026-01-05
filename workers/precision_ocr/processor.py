"""
정밀 OCR 처리기 - Chandra VLM 기반 (GPU)

Chandra: https://github.com/datalab-to/chandra
- Qwen3-VL 기반 고정밀 문서 OCR
- 표, 수식, 손글씨, 다단 레이아웃 지원
- vLLM 서버를 통한 GPU 추론
"""
import os
import re
import json
import base64
import logging
from io import BytesIO
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import httpx
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


class VLMClient:
    """
    vLLM OpenAI 호환 API 클라이언트

    Chandra VLM 서버와 통신하여 GPU 기반 OCR 수행
    """

    # OCR 프롬프트 템플릿
    OCR_PROMPT = """You are an advanced OCR system. Extract ALL text from this document image.

Instructions:
1. Preserve the original document structure (headings, paragraphs, lists, tables)
2. Output in clean Markdown format
3. For tables, use proper Markdown table syntax with | separators
4. Preserve reading order from top to bottom, left to right
5. Include ALL visible text, numbers, and symbols
6. For Korean text, transcribe accurately without translation

Output the extracted content in Markdown format:"""

    OCR_LAYOUT_PROMPT = """You are an advanced document OCR and layout analysis system.

Analyze this document image and extract:
1. ALL text content with proper structure
2. Document layout information
3. Tables in Markdown format
4. Headers/footers if present

Output format: Clean Markdown preserving document structure.
For tables, use:
| Header1 | Header2 |
|---------|---------|
| Cell1   | Cell2   |

Extract the document content:"""

    def __init__(
        self,
        api_base: str = "http://localhost:8080/v1",
        model_name: str = "chandra",
        max_tokens: int = 8192,
        timeout: int = 120,
    ):
        """
        Args:
            api_base: vLLM 서버 API 기본 URL
            model_name: 모델 이름 (vLLM served-model-name)
            max_tokens: 최대 출력 토큰 수
            timeout: 요청 타임아웃 (초)
        """
        self.api_base = api_base.rstrip("/")
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """HTTP 클라이언트 지연 초기화"""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self):
        """클라이언트 종료"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def health_check(self) -> bool:
        """서버 상태 확인"""
        try:
            response = self.client.get(f"{self.api_base}/models")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"VLM health check failed: {e}")
            return False

    def _image_to_base64(self, image: Image.Image, max_dim: int = 2048) -> str:
        """PIL 이미지를 base64 문자열로 변환 (크기 제한 포함)"""
        # 이미지 크기가 max_dim을 초과하면 리사이즈
        if max(image.size) > max_dim:
            ratio = max_dim / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Image resized to {new_size}")

        buffer = BytesIO()
        # JPEG로 저장 (용량 최적화)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=95)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def ocr(
        self,
        image: Image.Image,
        prompt_type: str = "ocr_layout",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        이미지 OCR 수행

        Args:
            image: PIL 이미지
            prompt_type: 프롬프트 타입 ("ocr" 또는 "ocr_layout")
            custom_prompt: 사용자 정의 프롬프트 (선택)

        Returns:
            OCR 결과 텍스트 (Markdown 형식)
        """
        # 프롬프트 선택
        if custom_prompt:
            prompt = custom_prompt
        elif prompt_type == "ocr_layout":
            prompt = self.OCR_LAYOUT_PROMPT
        else:
            prompt = self.OCR_PROMPT

        # 이미지 base64 인코딩
        image_base64 = self._image_to_base64(image)

        # vLLM OpenAI 호환 API 요청 구성
        # Vision 모델용 멀티모달 메시지 형식
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.1,  # 낮은 temperature로 일관된 출력
        }

        try:
            response = self.client.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            logger.error(f"VLM request timeout after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"VLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"VLM OCR failed: {e}")
            raise


class ChandraOCRProcessor:
    """
    Chandra VLM 기반 정밀 OCR 프로세서 (GPU)

    vLLM 서버를 통해 GPU 기반 고정밀 OCR 수행
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        max_tokens: int = 8192,
        timeout: int = 120,
        dpi: int = 300,
    ):
        """
        Args:
            api_base: vLLM 서버 URL (기본: 환경변수 또는 localhost:8080)
            model_name: 모델 이름 (기본: chandra)
            max_tokens: 최대 출력 토큰 수
            timeout: 요청 타임아웃 (초)
            dpi: PDF 렌더링 해상도
        """
        self.api_base = api_base or os.getenv("VLM_API_BASE", "http://localhost:8080/v1")
        self.model_name = model_name or os.getenv("VLM_MODEL_NAME", "chandra")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.dpi = dpi

        self._client: Optional[VLMClient] = None

    @property
    def client(self) -> VLMClient:
        """VLM 클라이언트 지연 초기화"""
        if self._client is None:
            self._client = VLMClient(
                api_base=self.api_base,
                model_name=self.model_name,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
        return self._client

    def health_check(self) -> bool:
        """VLM 서버 상태 확인"""
        return self.client.health_check()

    def process_pdf(self, pdf_path: str) -> List[PageOCRResult]:
        """
        PDF 파일 정밀 OCR 처리

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            페이지별 OCR 결과 리스트
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # 고해상도 렌더링
        images = convert_from_path(pdf_path, dpi=self.dpi)
        results = []

        for page_no, image in enumerate(images, start=1):
            logger.info(f"Processing page {page_no}/{len(images)}")
            result = self._process_image(image, page_no)
            results.append(result)

        return results

    def process_image(self, image_path: str) -> PageOCRResult:
        """
        이미지 파일 정밀 OCR 처리

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
        이미지 정밀 OCR 처리 (내부)
        """
        width, height = image.size

        # VLM OCR 실행
        markdown_text = self.client.ocr(image, prompt_type="ocr_layout")

        # 결과 파싱
        raw_text = self._extract_plain_text(markdown_text)
        html_text = self._markdown_to_html(markdown_text)
        blocks = self._parse_blocks_from_markdown(markdown_text, width, height)

        # 평균 confidence 계산 (VLM은 일반적으로 높은 정확도)
        confidences = [b.confidence for b in blocks if b.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.95

        return PageOCRResult(
            page_no=page_no,
            width=width,
            height=height,
            blocks=blocks,
            raw_text=raw_text,
            markdown=markdown_text,
            html=html_text,
            confidence=avg_confidence,
            layout_score=0.9,
        )

    def _extract_plain_text(self, markdown: str) -> str:
        """Markdown에서 순수 텍스트 추출"""
        text = markdown
        # 마크다운 문법 제거
        text = re.sub(r"#+\s*", "", text)  # 헤더
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # 볼드
        text = re.sub(r"\*([^*]+)\*", r"\1", text)  # 이탤릭
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # 링크
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)  # 이미지
        text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)  # 코드 블록
        text = re.sub(r"`([^`]+)`", r"\1", text)  # 인라인 코드
        text = re.sub(r"\|[^\n]+\|", "", text)  # 테이블 행
        text = re.sub(r"[-*]\s+", "", text)  # 리스트
        text = re.sub(r"\n{3,}", "\n\n", text)  # 다중 줄바꿈
        return text.strip()

    def _markdown_to_html(self, markdown: str) -> str:
        """간단한 Markdown to HTML 변환"""
        html = markdown

        # 헤더
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # 볼드/이탤릭
        html = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html)

        # 줄바꿈
        html = re.sub(r"\n\n", r"</p><p>", html)
        html = f"<p>{html}</p>"

        return html

    def _parse_blocks_from_markdown(
        self, markdown: str, page_width: int, page_height: int
    ) -> List[OCRBlock]:
        """Markdown에서 블록 구조 추출"""
        blocks = []
        lines = markdown.split("\n")
        current_block = []
        current_type = "text"
        block_order = 0

        for line in lines:
            stripped = line.strip()

            if not stripped:
                # 빈 줄 - 블록 구분
                if current_block:
                    text = "\n".join(current_block)
                    blocks.append(
                        OCRBlock(
                            text=text,
                            bbox=[0.05, 0.05, 0.95, 0.95],
                            confidence=0.95,
                            block_type=current_type,
                            reading_order=block_order,
                        )
                    )
                    block_order += 1
                    current_block = []
                    current_type = "text"
                continue

            # 블록 타입 감지
            if stripped.startswith("#"):
                if current_block:
                    blocks.append(
                        OCRBlock(
                            text="\n".join(current_block),
                            bbox=[0.05, 0.05, 0.95, 0.95],
                            confidence=0.95,
                            block_type=current_type,
                            reading_order=block_order,
                        )
                    )
                    block_order += 1
                    current_block = []

                # 헤더 블록
                header_text = re.sub(r"^#+\s*", "", stripped)
                blocks.append(
                    OCRBlock(
                        text=header_text,
                        bbox=[0.05, 0.05, 0.95, 0.95],
                        confidence=0.95,
                        block_type="header",
                        reading_order=block_order,
                    )
                )
                block_order += 1
                continue

            if stripped.startswith("|") and stripped.endswith("|"):
                # 테이블 행
                if current_type != "table":
                    if current_block:
                        blocks.append(
                            OCRBlock(
                                text="\n".join(current_block),
                                bbox=[0.05, 0.05, 0.95, 0.95],
                                confidence=0.95,
                                block_type=current_type,
                                reading_order=block_order,
                            )
                        )
                        block_order += 1
                        current_block = []
                    current_type = "table"
                current_block.append(stripped)
                continue

            if stripped.startswith(("-", "*", "+")) and len(stripped) > 2 and stripped[1] == " ":
                # 리스트 아이템
                if current_type != "list":
                    if current_block:
                        blocks.append(
                            OCRBlock(
                                text="\n".join(current_block),
                                bbox=[0.05, 0.05, 0.95, 0.95],
                                confidence=0.95,
                                block_type=current_type,
                                reading_order=block_order,
                            )
                        )
                        block_order += 1
                        current_block = []
                    current_type = "list"
                current_block.append(stripped)
                continue

            # 일반 텍스트
            if current_type == "table":
                # 테이블 종료
                if current_block:
                    table = self._parse_markdown_table(current_block)
                    blocks.append(
                        OCRBlock(
                            text="\n".join(current_block),
                            bbox=[0.05, 0.05, 0.95, 0.95],
                            confidence=0.95,
                            block_type="table",
                            table=table,
                            reading_order=block_order,
                        )
                    )
                    block_order += 1
                    current_block = []
                current_type = "text"

            current_block.append(stripped)

        # 마지막 블록 처리
        if current_block:
            table = None
            if current_type == "table":
                table = self._parse_markdown_table(current_block)

            blocks.append(
                OCRBlock(
                    text="\n".join(current_block),
                    bbox=[0.05, 0.05, 0.95, 0.95],
                    confidence=0.95,
                    block_type=current_type,
                    table=table,
                    reading_order=block_order,
                )
            )

        return blocks

    def _parse_markdown_table(self, table_lines: List[str]) -> Optional[Table]:
        """Markdown 테이블 파싱"""
        if not table_lines:
            return None

        rows = []
        for line in table_lines:
            # 구분선 스킵
            if re.match(r"^\|[\s\-:]+\|$", line):
                continue

            # 셀 추출
            cells = [
                cell.strip()
                for cell in line.split("|")
                if cell.strip()
            ]
            if cells:
                rows.append(cells)

        if not rows:
            return None

        return Table(
            rows=rows,
            bbox=[0.05, 0.05, 0.95, 0.95],
            confidence=0.95,
        )


def create_processor(
    api_base: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs
) -> ChandraOCRProcessor:
    """
    OCR 프로세서 팩토리 함수

    Args:
        api_base: vLLM 서버 URL
        model_name: 모델 이름
        **kwargs: 추가 설정

    Returns:
        ChandraOCRProcessor 인스턴스
    """
    return ChandraOCRProcessor(
        api_base=api_base,
        model_name=model_name,
        **kwargs
    )
