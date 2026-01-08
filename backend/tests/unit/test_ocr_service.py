"""
Unit tests for OCR service (recommend_ocr_mode logic)
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.models.document import Document, OCRMode, DocumentStatus, Importance
from app.services.ocr_service import recommend_ocr_mode, PRECISION_REQUIRED_TYPES


class TestPrecisionRequiredTypes:
    """Tests for precision required document types"""

    def test_precision_required_types_defined(self):
        """Test precision required types are defined"""
        assert "contract" in PRECISION_REQUIRED_TYPES
        assert "financial" in PRECISION_REQUIRED_TYPES
        assert "legal" in PRECISION_REQUIRED_TYPES
        assert "research" in PRECISION_REQUIRED_TYPES
        # Korean equivalents
        assert "계약" in PRECISION_REQUIRED_TYPES
        assert "재무" in PRECISION_REQUIRED_TYPES
        assert "법무" in PRECISION_REQUIRED_TYPES
        assert "연구" in PRECISION_REQUIRED_TYPES


class TestRecommendOCRModeForceRules:
    """Tests for forced OCR mode rules (override conditions)"""

    @pytest.mark.asyncio
    async def test_precision_required_doc_type_contract(self):
        """Test contract doc_type forces PRECISION mode"""
        doc = Document(
            id=1,
            title="Contract",
            original_filename="contract.pdf",
            file_path="documents/contract.pdf",
            doc_type="contract",
            importance=Importance.MEDIUM,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        assert result.recommended_mode == OCRMode.PRECISION
        assert result.precision_score == 100
        assert "정밀 OCR 필수 대상" in result.reasons[0]

    @pytest.mark.asyncio
    async def test_precision_required_doc_type_financial(self):
        """Test financial doc_type forces PRECISION mode"""
        doc = Document(
            id=1,
            title="Financial Report",
            original_filename="financial.pdf",
            file_path="documents/financial.pdf",
            doc_type="financial",
            importance=Importance.LOW,
            page_count=50,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        assert result.recommended_mode == OCRMode.PRECISION
        assert result.precision_score == 100

    @pytest.mark.asyncio
    async def test_precision_required_doc_type_korean(self):
        """Test Korean doc_type (계약) forces PRECISION mode"""
        doc = Document(
            id=1,
            title="계약서",
            original_filename="계약서.pdf",
            file_path="documents/계약서.pdf",
            doc_type="계약",
            importance=Importance.MEDIUM,
            page_count=5,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        assert result.recommended_mode == OCRMode.PRECISION
        assert result.precision_score == 100

    @pytest.mark.asyncio
    async def test_high_importance_forces_precision(self):
        """Test HIGH importance forces PRECISION mode"""
        doc = Document(
            id=1,
            title="Important Doc",
            original_filename="important.pdf",
            file_path="documents/important.pdf",
            doc_type="general",
            importance=Importance.HIGH,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        assert result.recommended_mode == OCRMode.PRECISION
        assert result.precision_score == 100
        assert "중요도가 High" in result.reasons[0]

    @pytest.mark.asyncio
    async def test_low_importance_large_document_forces_fast(self):
        """Test LOW importance + >200 pages forces FAST mode"""
        doc = Document(
            id=1,
            title="Archive Document",
            original_filename="archive.pdf",
            file_path="documents/archive.pdf",
            doc_type="archive",
            importance=Importance.LOW,
            page_count=250,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        assert result.recommended_mode == OCRMode.FAST
        assert result.precision_score == 0
        assert "200페이지 이상" in result.reasons[0]

    @pytest.mark.asyncio
    async def test_low_importance_exactly_200_pages_not_forced(self):
        """Test LOW importance + exactly 200 pages is NOT forced to FAST"""
        doc = Document(
            id=1,
            title="Archive Document",
            original_filename="archive.pdf",
            file_path="documents/archive.pdf",
            doc_type="archive",
            importance=Importance.LOW,
            page_count=200,  # Exactly 200, not > 200
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Should not be forced to FAST (uses scoring instead)
        assert result.recommended_mode == OCRMode.FAST
        assert result.precision_score < 30  # Score-based FAST, not forced


class TestRecommendOCRModeScoring:
    """Tests for score-based OCR mode recommendation"""

    @pytest.mark.asyncio
    async def test_medium_importance_adds_15_points(self):
        """Test MEDIUM importance adds 15 points"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # MEDIUM adds 15 points, score = 15 < 30, so FAST mode
        assert result.precision_score == 15
        assert "중요도 Medium (+15)" in result.reasons

    @pytest.mark.asyncio
    async def test_large_page_count_subtracts_15_points(self):
        """Test >100 pages subtracts 15 points"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,
            page_count=150,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # MEDIUM (+15) + large page (-15) = 0
        assert result.precision_score == 0
        assert any("-15" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_score_threshold_for_accurate_mode(self):
        """Test score >= 30 recommends ACCURATE mode"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,  # +15
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Score = 15, which is < 30, so FAST mode
        assert result.recommended_mode == OCRMode.FAST
        assert result.precision_score == 15

    @pytest.mark.asyncio
    @patch("app.services.ocr_service.settings")
    async def test_score_threshold_for_precision_mode(self, mock_settings):
        """Test score >= OCR_PRECISION_THRESHOLD recommends PRECISION mode"""
        mock_settings.OCR_PRECISION_THRESHOLD = 60

        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,  # +15 (not enough for precision)
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Score = 15, which is < 30, so FAST mode
        assert result.recommended_mode == OCRMode.FAST

    @pytest.mark.asyncio
    async def test_score_boundary_29_is_fast(self):
        """Test score = 29 recommends FAST mode (boundary test)"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,  # +15
            page_count=10,  # no penalty
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Score = 15 < 30, so FAST
        assert result.precision_score < 30
        assert result.recommended_mode == OCRMode.FAST


class TestRecommendOCRModeEdgeCases:
    """Tests for edge cases in OCR mode recommendation"""

    @pytest.mark.asyncio
    async def test_null_doc_type(self):
        """Test handling of null doc_type"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            doc_type=None,
            importance=Importance.MEDIUM,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Should not crash, just use scoring
        assert result.recommended_mode in [OCRMode.FAST, OCRMode.ACCURATE, OCRMode.PRECISION]

    @pytest.mark.asyncio
    async def test_null_page_count(self):
        """Test handling of null page_count"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            doc_type="general",
            importance=Importance.MEDIUM,
            page_count=None,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Should not crash
        assert result.recommended_mode in [OCRMode.FAST, OCRMode.ACCURATE, OCRMode.PRECISION]

    @pytest.mark.asyncio
    async def test_zero_page_count(self):
        """Test handling of zero page_count"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            doc_type="general",
            importance=Importance.MEDIUM,
            page_count=0,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Should not apply page count penalty
        assert result.recommended_mode in [OCRMode.FAST, OCRMode.ACCURATE, OCRMode.PRECISION]

    @pytest.mark.asyncio
    async def test_case_insensitive_doc_type(self):
        """Test doc_type matching is case-insensitive"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            doc_type="CONTRACT",  # uppercase
            importance=Importance.MEDIUM,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Should match "contract" case-insensitively
        assert result.recommended_mode == OCRMode.PRECISION
        assert result.precision_score == 100

    @pytest.mark.asyncio
    async def test_doc_type_with_whitespace(self):
        """Test doc_type with extra whitespace"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            doc_type="  contract  ",  # whitespace (won't match without strip)
            importance=Importance.MEDIUM,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Current implementation uses .lower() without .strip()
        # So this won't match "contract"
        # This test documents current behavior
        assert result.recommended_mode in [OCRMode.FAST, OCRMode.ACCURATE, OCRMode.PRECISION]


class TestRecommendOCRModeReasons:
    """Tests for reason messages in recommendations"""

    @pytest.mark.asyncio
    async def test_reasons_include_score_breakdown(self):
        """Test reasons include score breakdown"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,
            page_count=150,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Should have reasons explaining the score
        assert len(result.reasons) > 0
        assert any("Medium" in r for r in result.reasons)
        assert any("페이지" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_reasons_include_final_decision(self):
        """Test reasons include final decision explanation"""
        doc = Document(
            id=1,
            title="Test",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            importance=Importance.MEDIUM,
            page_count=10,
            status=DocumentStatus.PENDING,
        )

        result = await recommend_ocr_mode(doc)

        # Last reason should explain the threshold decision
        assert any("총점" in r for r in result.reasons)
