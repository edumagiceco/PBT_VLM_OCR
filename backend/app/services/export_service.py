from typing import Tuple
import json

from app.models.document import Document


async def export_document(document: Document, format: str) -> Tuple[bytes, str, str]:
    """
    문서 내보내기 (md/json/html)

    Returns:
        Tuple[content, content_type, filename]
    """
    base_filename = document.title.replace(" ", "_")

    if format == "md":
        content = await _export_markdown(document)
        return content.encode("utf-8"), "text/markdown", f"{base_filename}.md"

    elif format == "json":
        content = await _export_json(document)
        return content.encode("utf-8"), "application/json", f"{base_filename}.json"

    elif format == "html":
        content = await _export_html(document)
        return content.encode("utf-8"), "text/html", f"{base_filename}.html"

    raise ValueError(f"Unsupported format: {format}")


async def _export_markdown(document: Document) -> str:
    """Markdown 형식으로 내보내기"""
    lines = [f"# {document.title}\n"]

    if document.department:
        lines.append(f"**부서**: {document.department}\n")

    ocr_mode = document.ocr_mode.value if hasattr(document.ocr_mode, 'value') else document.ocr_mode
    lines.append(f"**OCR 모드**: {ocr_mode}\n")
    lines.append("---\n")

    for page in sorted(document.pages, key=lambda p: p.page_no):
        lines.append(f"\n## Page {page.page_no}\n")

        for block in sorted(page.blocks, key=lambda b: b.block_order):
            block_type = block.block_type.value if hasattr(block.block_type, 'value') else block.block_type
            if block_type.upper() == "TABLE" and block.table_json:
                lines.append(_table_to_markdown(block.table_json))
            elif block.text:
                lines.append(f"{block.text}\n")

    return "\n".join(lines)


async def _export_json(document: Document) -> str:
    """JSON 형식으로 내보내기"""
    result = {
        "document": {
            "id": document.id,
            "title": document.title,
            "department": document.department,
            "doc_type": document.doc_type,
            "ocr_mode": document.ocr_mode.value if hasattr(document.ocr_mode, 'value') else document.ocr_mode,
            "page_count": document.page_count,
        },
        "pages": [],
    }

    for page in sorted(document.pages, key=lambda p: p.page_no):
        page_data = {
            "page_no": page.page_no,
            "width": page.width,
            "height": page.height,
            "confidence": page.confidence,
            "blocks": [],
        }

        for block in sorted(page.blocks, key=lambda b: b.block_order):
            block_type = block.block_type.value if hasattr(block.block_type, 'value') else block.block_type
            page_data["blocks"].append({
                "type": block_type,
                "bbox": block.bbox,
                "text": block.text,
                "table": block.table_json,
                "confidence": block.confidence,
            })

        result["pages"].append(page_data)

    return json.dumps(result, ensure_ascii=False, indent=2)


async def _export_html(document: Document) -> str:
    """HTML 형식으로 내보내기"""
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='ko'>",
        "<head>",
        "<meta charset='UTF-8'>",
        f"<title>{document.title}</title>",
        "<style>",
        "body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
        "table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #f4f4f4; }",
        ".page { margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid #eee; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{document.title}</h1>",
    ]

    if document.department:
        html_parts.append(f"<p><strong>부서</strong>: {document.department}</p>")

    ocr_mode = document.ocr_mode.value if hasattr(document.ocr_mode, 'value') else document.ocr_mode
    html_parts.append(f"<p><strong>OCR 모드</strong>: {ocr_mode}</p>")
    html_parts.append("<hr>")

    for page in sorted(document.pages, key=lambda p: p.page_no):
        html_parts.append(f"<div class='page'>")
        html_parts.append(f"<h2>Page {page.page_no}</h2>")

        for block in sorted(page.blocks, key=lambda b: b.block_order):
            block_type = block.block_type.value if hasattr(block.block_type, 'value') else block.block_type
            if block_type.upper() == "TABLE" and block.table_json:
                html_parts.append(_table_to_html(block.table_json))
            elif block.text:
                html_parts.append(f"<p>{block.text}</p>")

        html_parts.append("</div>")

    html_parts.extend(["</body>", "</html>"])

    return "\n".join(html_parts)


def _table_to_markdown(table_json: dict) -> str:
    """테이블 JSON을 Markdown 표로 변환"""
    if not table_json or "rows" not in table_json:
        return ""

    rows = table_json["rows"]
    if not rows:
        return ""

    lines = []
    # Header
    header = rows[0]
    lines.append("| " + " | ".join(str(cell) for cell in header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")

    # Body
    for row in rows[1:]:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return "\n".join(lines) + "\n"


def _table_to_html(table_json: dict) -> str:
    """테이블 JSON을 HTML 표로 변환"""
    if not table_json or "rows" not in table_json:
        return ""

    rows = table_json["rows"]
    if not rows:
        return ""

    html = ["<table>"]

    # Header
    html.append("<thead><tr>")
    for cell in rows[0]:
        html.append(f"<th>{cell}</th>")
    html.append("</tr></thead>")

    # Body
    html.append("<tbody>")
    for row in rows[1:]:
        html.append("<tr>")
        for cell in row:
            html.append(f"<td>{cell}</td>")
        html.append("</tr>")
    html.append("</tbody>")

    html.append("</table>")
    return "\n".join(html)
