from typing import List
from app.models.document import Document, OCRMode, Importance
from app.schemas.document import OCRModeRecommendation
from app.core.config import settings

# 문서 유형별 정밀 OCR 필요 여부
PRECISION_REQUIRED_TYPES = ["contract", "financial", "legal", "research", "계약", "재무", "법무", "연구"]


async def recommend_ocr_mode(document: Document) -> OCRModeRecommendation:
    """
    OCR 모드 자동 추천 로직

    OCR 모드:
    - FAST: Tesseract 기반 (CPU, 빠른 처리)
    - ACCURATE: PaddleOCR 기반 (딥러닝, 높은 정확도)
    - PRECISION: Chandra VLM 기반 (GPU, 최고 정밀도)

    PRD 기준:
    - 무조건 결정 규칙 (Override) 우선 적용
    - 점수 기반 추천 (precision_score >= 60 → 정밀 OCR, >= 30 → 정확 OCR)
    """
    reasons = []
    precision_score = 0

    # 1. 무조건 정밀 OCR 강제 조건
    if document.doc_type and document.doc_type.lower() in PRECISION_REQUIRED_TYPES:
        return OCRModeRecommendation(
            recommended_mode=OCRMode.PRECISION,
            precision_score=100,
            reasons=[f"문서 유형({document.doc_type})이 정밀 OCR 필수 대상입니다."],
        )

    if document.importance == Importance.HIGH:
        return OCRModeRecommendation(
            recommended_mode=OCRMode.PRECISION,
            precision_score=100,
            reasons=["중요도가 High로 설정되어 정밀 OCR이 권장됩니다."],
        )

    # 2. 무조건 빠른 OCR 강제 조건
    if document.importance == Importance.LOW and document.page_count and document.page_count > 200:
        return OCRModeRecommendation(
            recommended_mode=OCRMode.FAST,
            precision_score=0,
            reasons=["중요도 Low + 200페이지 이상으로 빠른 OCR이 적합합니다."],
        )

    # 3. 점수 기반 추천
    # 중요도 점수 (+30)
    if document.importance == Importance.HIGH:
        precision_score += 30
        reasons.append("중요도 High (+30)")
    elif document.importance == Importance.MEDIUM:
        precision_score += 15
        reasons.append("중요도 Medium (+15)")

    # 문서 유형 점수 (+25)
    if document.doc_type and document.doc_type.lower() in PRECISION_REQUIRED_TYPES:
        precision_score += 25
        reasons.append(f"문서 유형 {document.doc_type} (+25)")

    # 페이지 수 감점 (-15)
    if document.page_count and document.page_count > 100:
        precision_score -= 15
        reasons.append(f"페이지 수 {document.page_count}p (-15)")

    # TODO: 스캔본 감지 (+20)
    # TODO: 표/다단 감지 (+20)

    # 추천 모드 결정 (3단계)
    if precision_score >= settings.OCR_PRECISION_THRESHOLD:
        recommended_mode = OCRMode.PRECISION
        reasons.append(f"총점 {precision_score}점 >= 정밀 임계값 {settings.OCR_PRECISION_THRESHOLD}")
    elif precision_score >= 30:
        recommended_mode = OCRMode.ACCURATE
        reasons.append(f"총점 {precision_score}점 >= 정확 임계값 30")
    else:
        recommended_mode = OCRMode.FAST
        reasons.append(f"총점 {precision_score}점 < 정확 임계값 30")

    return OCRModeRecommendation(
        recommended_mode=recommended_mode,
        precision_score=precision_score,
        reasons=reasons,
    )


async def pre_ocr_quality_check(document: Document) -> float:
    """
    프리 OCR 기반 품질 점검 (선택적)
    1~2페이지 일반 OCR 샘플로 품질 점수 측정
    품질 점수 < 0.75 → 정밀 OCR 상향
    """
    # TODO: 구현
    return 1.0
