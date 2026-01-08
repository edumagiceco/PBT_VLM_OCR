"""
Unit tests for export service (document export to md/json/html)
"""
import json
import pytest
from datetime import datetime

from app.models.document import (
    Document, DocumentPage, DocumentBlock,
    OCRMode, DocumentStatus, Importance, BlockType
)
from app.services.export_service import (
    export_document,
    _export_markdown,
    _export_json,
    _export_html,
    _table_to_markdown,
    _table_to_html,
)


class TestTableToMarkdown:
    """Tests for _table_to_markdown function"""

    def test_basic_table_conversion(self, sample_table_json):
        """Test basic table to markdown conversion"""
        result = _table_to_markdown(sample_table_json)

        assert "| Name | Age | City |" in result
        assert "| --- | --- | --- |" in result
        assert "| Alice | 30 | Seoul |" in result
        assert "| Bob | 25 | Busan |" in result

    def test_empty_rows(self, empty_table_json):
        """Test empty table returns empty string"""
        result = _table_to_markdown(empty_table_json)
        assert result == ""

    def test_none_table_json(self):
        """Test None table_json returns empty string"""
        result = _table_to_markdown(None)
        assert result == ""

    def test_missing_rows_key(self):
        """Test table_json without 'rows' key returns empty string"""
        result = _table_to_markdown({"columns": ["A", "B"]})
        assert result == ""

    def test_single_row_table(self):
        """Test table with only header row"""
        table = {"rows": [["Header 1", "Header 2"]]}
        result = _table_to_markdown(table)

        assert "| Header 1 | Header 2 |" in result
        assert "| --- | --- |" in result

    def test_table_with_empty_cells(self):
        """Test table with empty cell values"""
        table = {
            "rows": [
                ["Name", "Value"],
                ["Item", ""],
            ]
        }
        result = _table_to_markdown(table)

        assert "| Item |  |" in result

    def test_table_with_numeric_values(self):
        """Test table with numeric values"""
        table = {
            "rows": [
                ["Count", "Price"],
                [10, 99.99],
            ]
        }
        result = _table_to_markdown(table)

        assert "| 10 | 99.99 |" in result


class TestTableToHtml:
    """Tests for _table_to_html function"""

    def test_basic_table_conversion(self, sample_table_json):
        """Test basic table to HTML conversion"""
        result = _table_to_html(sample_table_json)

        assert "<table>" in result
        assert "</table>" in result
        assert "<thead>" in result
        assert "</thead>" in result
        assert "<tbody>" in result
        assert "</tbody>" in result
        assert "<th>Name</th>" in result
        assert "<td>Alice</td>" in result

    def test_empty_rows(self, empty_table_json):
        """Test empty table returns empty string"""
        result = _table_to_html(empty_table_json)
        assert result == ""

    def test_none_table_json(self):
        """Test None table_json returns empty string"""
        result = _table_to_html(None)
        assert result == ""

    def test_header_uses_th_tags(self):
        """Test header row uses <th> tags"""
        table = {"rows": [["Header 1", "Header 2"], ["Data 1", "Data 2"]]}
        result = _table_to_html(table)

        assert "<th>Header 1</th>" in result
        assert "<th>Header 2</th>" in result

    def test_body_uses_td_tags(self):
        """Test body rows use <td> tags"""
        table = {"rows": [["Header 1", "Header 2"], ["Data 1", "Data 2"]]}
        result = _table_to_html(table)

        assert "<td>Data 1</td>" in result
        assert "<td>Data 2</td>" in result


class TestExportMarkdown:
    """Tests for _export_markdown function"""

    @pytest.mark.asyncio
    async def test_export_markdown_basic(self, document_with_pages):
        """Test basic markdown export"""
        result = await _export_markdown(document_with_pages)

        assert "# Test Document" in result
        assert "## Page 1" in result

    @pytest.mark.asyncio
    async def test_export_markdown_includes_department(self, document_with_pages):
        """Test markdown includes department"""
        result = await _export_markdown(document_with_pages)

        assert "**부서**: Engineering" in result

    @pytest.mark.asyncio
    async def test_export_markdown_includes_ocr_mode(self, document_with_pages):
        """Test markdown includes OCR mode"""
        result = await _export_markdown(document_with_pages)

        assert "**OCR 모드**:" in result

    @pytest.mark.asyncio
    async def test_export_markdown_includes_text_blocks(self, document_with_pages):
        """Test markdown includes text from blocks"""
        result = await _export_markdown(document_with_pages)

        assert "Sample block text" in result

    @pytest.mark.asyncio
    async def test_export_markdown_includes_table(self, document_with_pages):
        """Test markdown includes table content"""
        result = await _export_markdown(document_with_pages)

        assert "| Header 1 | Header 2 | Header 3 |" in result

    @pytest.mark.asyncio
    async def test_export_markdown_without_department(self):
        """Test markdown without department"""
        doc = Document(
            id=1,
            title="No Dept",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            department=None,
            ocr_mode="auto",
            status=DocumentStatus.PENDING,
        )
        doc.pages = []

        result = await _export_markdown(doc)

        assert "**부서**:" not in result

    @pytest.mark.asyncio
    async def test_export_markdown_empty_pages(self):
        """Test markdown with no pages"""
        doc = Document(
            id=1,
            title="Empty Doc",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            department="Test",
            ocr_mode="auto",
            status=DocumentStatus.PENDING,
        )
        doc.pages = []

        result = await _export_markdown(doc)

        assert "# Empty Doc" in result
        assert "## Page" not in result


class TestExportJson:
    """Tests for _export_json function"""

    @pytest.mark.asyncio
    async def test_export_json_valid_format(self, document_with_pages):
        """Test JSON export produces valid JSON"""
        result = await _export_json(document_with_pages)
        parsed = json.loads(result)

        assert "document" in parsed
        assert "pages" in parsed

    @pytest.mark.asyncio
    async def test_export_json_document_fields(self, document_with_pages):
        """Test JSON includes document fields"""
        result = await _export_json(document_with_pages)
        parsed = json.loads(result)

        doc = parsed["document"]
        assert doc["id"] == 1
        assert doc["title"] == "Test Document"
        assert doc["department"] == "Engineering"

    @pytest.mark.asyncio
    async def test_export_json_pages_structure(self, document_with_pages):
        """Test JSON includes pages with correct structure"""
        result = await _export_json(document_with_pages)
        parsed = json.loads(result)

        assert len(parsed["pages"]) == 1
        page = parsed["pages"][0]
        assert page["page_no"] == 1
        assert page["width"] == 800
        assert page["height"] == 1200
        assert "blocks" in page

    @pytest.mark.asyncio
    async def test_export_json_blocks_structure(self, document_with_pages):
        """Test JSON includes blocks with correct structure"""
        result = await _export_json(document_with_pages)
        parsed = json.loads(result)

        blocks = parsed["pages"][0]["blocks"]
        assert len(blocks) == 2

        text_block = blocks[0]
        assert text_block["type"] == "TEXT"
        assert text_block["text"] == "Sample block text"
        assert text_block["bbox"] == [0.1, 0.1, 0.9, 0.2]

        table_block = blocks[1]
        assert table_block["type"] == "TABLE"
        assert table_block["table"] is not None

    @pytest.mark.asyncio
    async def test_export_json_korean_encoding(self):
        """Test JSON handles Korean text correctly"""
        doc = Document(
            id=1,
            title="한글 문서",
            original_filename="korean.pdf",
            file_path="documents/korean.pdf",
            department="개발팀",
            ocr_mode="auto",
            status=DocumentStatus.PENDING,
        )
        doc.pages = []

        result = await _export_json(doc)
        parsed = json.loads(result)

        assert parsed["document"]["title"] == "한글 문서"
        assert parsed["document"]["department"] == "개발팀"


class TestExportHtml:
    """Tests for _export_html function"""

    @pytest.mark.asyncio
    async def test_export_html_valid_structure(self, document_with_pages):
        """Test HTML has valid structure"""
        result = await _export_html(document_with_pages)

        assert "<!DOCTYPE html>" in result
        assert "<html lang='ko'>" in result
        assert "<head>" in result
        assert "</head>" in result
        assert "<body>" in result
        assert "</body>" in result
        assert "</html>" in result

    @pytest.mark.asyncio
    async def test_export_html_title(self, document_with_pages):
        """Test HTML includes title"""
        result = await _export_html(document_with_pages)

        assert "<title>Test Document</title>" in result
        assert "<h1>Test Document</h1>" in result

    @pytest.mark.asyncio
    async def test_export_html_includes_department(self, document_with_pages):
        """Test HTML includes department"""
        result = await _export_html(document_with_pages)

        assert "<strong>부서</strong>: Engineering" in result

    @pytest.mark.asyncio
    async def test_export_html_includes_ocr_mode(self, document_with_pages):
        """Test HTML includes OCR mode"""
        result = await _export_html(document_with_pages)

        assert "<strong>OCR 모드</strong>:" in result

    @pytest.mark.asyncio
    async def test_export_html_includes_css(self, document_with_pages):
        """Test HTML includes CSS styles"""
        result = await _export_html(document_with_pages)

        assert "<style>" in result
        assert "font-family:" in result
        assert "table {" in result

    @pytest.mark.asyncio
    async def test_export_html_page_divs(self, document_with_pages):
        """Test HTML has page divs"""
        result = await _export_html(document_with_pages)

        assert "<div class='page'>" in result
        assert "<h2>Page 1</h2>" in result

    @pytest.mark.asyncio
    async def test_export_html_text_in_paragraphs(self, document_with_pages):
        """Test HTML puts text in paragraphs"""
        result = await _export_html(document_with_pages)

        assert "<p>Sample block text</p>" in result

    @pytest.mark.asyncio
    async def test_export_html_table_rendered(self, document_with_pages):
        """Test HTML renders tables"""
        result = await _export_html(document_with_pages)

        assert "<table>" in result
        assert "<th>Header 1</th>" in result


class TestExportDocument:
    """Tests for main export_document function"""

    @pytest.mark.asyncio
    async def test_export_document_markdown(self, document_with_pages):
        """Test export to markdown format"""
        content, content_type, filename = await export_document(document_with_pages, "md")

        assert content_type == "text/markdown"
        assert filename == "Test_Document.md"
        assert isinstance(content, bytes)
        assert b"# Test Document" in content

    @pytest.mark.asyncio
    async def test_export_document_json(self, document_with_pages):
        """Test export to JSON format"""
        content, content_type, filename = await export_document(document_with_pages, "json")

        assert content_type == "application/json"
        assert filename == "Test_Document.json"
        assert isinstance(content, bytes)

        parsed = json.loads(content.decode("utf-8"))
        assert "document" in parsed

    @pytest.mark.asyncio
    async def test_export_document_html(self, document_with_pages):
        """Test export to HTML format"""
        content, content_type, filename = await export_document(document_with_pages, "html")

        assert content_type == "text/html"
        assert filename == "Test_Document.html"
        assert isinstance(content, bytes)
        assert b"<!DOCTYPE html>" in content

    @pytest.mark.asyncio
    async def test_export_document_unsupported_format(self, document_with_pages):
        """Test unsupported format raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            await export_document(document_with_pages, "pdf")

        assert "Unsupported format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_export_document_filename_spaces_replaced(self):
        """Test filename has spaces replaced with underscores"""
        doc = Document(
            id=1,
            title="My Test Document",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            ocr_mode="auto",
            status=DocumentStatus.PENDING,
        )
        doc.pages = []

        content, content_type, filename = await export_document(doc, "md")

        assert filename == "My_Test_Document.md"

    @pytest.mark.asyncio
    async def test_export_document_utf8_encoding(self):
        """Test content is UTF-8 encoded"""
        doc = Document(
            id=1,
            title="한글 제목",
            original_filename="test.pdf",
            file_path="documents/test.pdf",
            ocr_mode="auto",
            status=DocumentStatus.PENDING,
        )
        doc.pages = []

        content, content_type, filename = await export_document(doc, "md")

        decoded = content.decode("utf-8")
        assert "# 한글 제목" in decoded
