# Backend API 테스트 케이스

## 1. 개요

| 항목 | 내용 |
|------|------|
| 테스트 대상 | FastAPI Backend REST API |
| 기본 URL | `http://{host}:8000/api/v1` |
| 테스트 도구 | pytest, httpx, curl |

---

## 2. 문서 API (`/documents`)

### TC-API-DOC-001: 문서 업로드 - PDF 파일

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-001 |
| **테스트명** | PDF 문서 업로드 |
| **우선순위** | High |
| **전제조건** | 백엔드 서버 실행, MinIO 연결 |

**테스트 절차:**
1. PDF 파일 준비 (예: `personnel_regulations.pdf`)
2. POST `/documents` 요청 전송
3. 응답 확인

**요청:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -F "file=@/path/to/personnel_regulations.pdf" \
  -F "title=인사규정" \
  -F "ocr_mode=fast"
```

**예상 결과:**
- 상태 코드: 201 Created
- 응답 body에 `id`, `title`, `status: "pending"` 포함
- MinIO에 파일 저장 확인

**검증 항목:**
- [ ] 응답 상태 코드 201
- [ ] `document.id` 존재
- [ ] `document.status == "pending"`
- [ ] `document.ocr_mode == "fast"`
- [ ] MinIO에 파일 존재

---

### TC-API-DOC-002: 문서 업로드 - 이미지 파일 (PNG)

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-002 |
| **테스트명** | PNG 이미지 업로드 |
| **우선순위** | High |

**테스트 절차:**
1. PNG 이미지 준비
2. POST `/documents` 요청

**요청:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -F "file=@/path/to/sample.png" \
  -F "title=샘플 이미지" \
  -F "ocr_mode=accurate"
```

**예상 결과:**
- 상태 코드: 201 Created
- `mime_type: "image/png"`

**검증 항목:**
- [ ] 응답 상태 코드 201
- [ ] MIME 타입 정확

---

### TC-API-DOC-003: 문서 업로드 - 지원하지 않는 파일 형식

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-003 |
| **테스트명** | 잘못된 파일 형식 업로드 |
| **우선순위** | Medium |

**테스트 절차:**
1. 지원하지 않는 파일 (예: `.exe`, `.zip`) 준비
2. POST `/documents` 요청

**예상 결과:**
- 상태 코드: 400 Bad Request
- 에러 메시지 반환

**검증 항목:**
- [ ] 응답 상태 코드 400
- [ ] 에러 메시지 명확

---

### TC-API-DOC-004: 문서 업로드 - OCR 모드별 테스트

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-004 |
| **테스트명** | 각 OCR 모드로 업로드 |
| **우선순위** | High |

**테스트 데이터:**

| OCR Mode | 예상 큐 |
|----------|---------|
| fast | fast_ocr |
| accurate | accurate_ocr |
| precision | precision_ocr |
| auto | fast_ocr (기본) |

**검증 항목:**
- [ ] `fast` 모드 정상 저장
- [ ] `accurate` 모드 정상 저장
- [ ] `precision` 모드 정상 저장
- [ ] `auto` 모드 정상 저장

---

### TC-API-DOC-005: 문서 목록 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-005 |
| **테스트명** | 문서 목록 조회 |
| **우선순위** | High |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents?page=1&page_size=20"
```

**예상 결과:**
- 상태 코드: 200 OK
- `total`, `page`, `page_size`, `items` 필드 포함

**검증 항목:**
- [ ] 응답 상태 코드 200
- [ ] 페이지네이션 정보 정확
- [ ] `items` 배열 반환

---

### TC-API-DOC-006: 문서 목록 - 검색 필터

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-006 |
| **테스트명** | 문서 검색 |
| **우선순위** | Medium |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents?search=인사"
```

**검증 항목:**
- [ ] 제목에 "인사" 포함된 문서만 반환
- [ ] 검색 결과 0개일 때 빈 배열

---

### TC-API-DOC-007: 문서 목록 - 상태 필터

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-007 |
| **테스트명** | 상태별 문서 필터 |
| **우선순위** | Medium |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents?status=completed"
```

**검증 항목:**
- [ ] `status=pending` 필터 동작
- [ ] `status=processing` 필터 동작
- [ ] `status=completed` 필터 동작
- [ ] `status=failed` 필터 동작

---

### TC-API-DOC-008: 문서 상세 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-008 |
| **테스트명** | 단일 문서 조회 |
| **우선순위** | High |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents/1"
```

**예상 결과:**
- 상태 코드: 200 OK
- 문서 상세 정보 반환 (pages, blocks 포함)

**검증 항목:**
- [ ] 문서 기본 정보 포함
- [ ] `pages` 배열 포함
- [ ] 각 페이지에 `blocks` 배열 포함

---

### TC-API-DOC-009: 존재하지 않는 문서 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-009 |
| **테스트명** | 없는 문서 조회 |
| **우선순위** | Medium |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents/99999"
```

**예상 결과:**
- 상태 코드: 404 Not Found

**검증 항목:**
- [ ] 응답 상태 코드 404
- [ ] 에러 메시지 반환

---

### TC-API-DOC-010: 문서 수정

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-010 |
| **테스트명** | 문서 정보 수정 |
| **우선순위** | Medium |

**요청:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/documents/1" \
  -H "Content-Type: application/json" \
  -d '{"title": "수정된 제목", "department": "인사팀"}'
```

**예상 결과:**
- 상태 코드: 200 OK
- 수정된 정보 반환

**검증 항목:**
- [ ] `title` 변경 확인
- [ ] `department` 변경 확인
- [ ] `updated_at` 갱신 확인

---

### TC-API-DOC-011: 문서 삭제

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-011 |
| **테스트명** | 문서 삭제 |
| **우선순위** | High |

**요청:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/1"
```

**예상 결과:**
- 상태 코드: 204 No Content
- DB에서 문서 삭제
- MinIO에서 파일 삭제

**검증 항목:**
- [ ] 응답 상태 코드 204
- [ ] DB에서 문서 조회 불가
- [ ] MinIO 파일 삭제 확인

---

### TC-API-DOC-012: OCR 재처리

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-012 |
| **테스트명** | OCR 재처리 요청 |
| **우선순위** | Medium |

**요청:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/1/reprocess?ocr_mode=precision"
```

**예상 결과:**
- 상태 코드: 200 OK
- 문서 상태가 `pending`으로 변경
- 새 OCR 모드 적용

**검증 항목:**
- [ ] `status` → `pending`
- [ ] `ocr_mode` 변경 확인
- [ ] 기존 페이지/블록 삭제

---

### TC-API-DOC-013: 블록 수정

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-013 |
| **테스트명** | OCR 블록 텍스트 수정 |
| **우선순위** | Medium |

**요청:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/documents/1/blocks/1" \
  -H "Content-Type: application/json" \
  -d '{"text": "수정된 텍스트"}'
```

**검증 항목:**
- [ ] 블록 텍스트 변경 확인
- [ ] `updated_at` 갱신

---

### TC-API-DOC-014: 문서 다운로드 - Markdown

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-014 |
| **테스트명** | Markdown 형식 다운로드 |
| **우선순위** | Medium |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents/1/download?format=md"
```

**예상 결과:**
- 상태 코드: 200 OK
- Content-Type: text/markdown
- Markdown 형식 텍스트

**검증 항목:**
- [ ] 마크다운 형식 정확
- [ ] 모든 페이지 텍스트 포함

---

### TC-API-DOC-015: 문서 다운로드 - JSON

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-015 |
| **테스트명** | JSON 형식 다운로드 |
| **우선순위** | Medium |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents/1/download?format=json"
```

**검증 항목:**
- [ ] 유효한 JSON
- [ ] 페이지/블록 구조 포함

---

### TC-API-DOC-016: 문서 다운로드 - HTML

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-016 |
| **테스트명** | HTML 형식 다운로드 |
| **우선순위** | Low |

**검증 항목:**
- [ ] 유효한 HTML
- [ ] 스타일 적용

---

### TC-API-DOC-017: 처리 대기열 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-DOC-017 |
| **테스트명** | 처리 현황 조회 |
| **우선순위** | High |

**요청:**
```bash
curl "http://localhost:8000/api/v1/documents/queue"
```

**예상 결과:**
- 상태 코드: 200 OK
- `total`, `pending`, `processing`, `completed`, `failed` 통계
- `items` 배열

**검증 항목:**
- [ ] 통계 정보 정확
- [ ] 항목 목록 반환

---

## 3. 파일 API (`/files`)

### TC-API-FILE-001: 페이지 이미지 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-FILE-001 |
| **테스트명** | 페이지 이미지 프록시 조회 |
| **우선순위** | High |

**요청:**
```bash
curl "http://localhost:8000/api/v1/files/documents/1/pages/1/image"
```

**예상 결과:**
- 상태 코드: 200 OK
- Content-Type: image/png
- 이미지 바이너리 반환

**검증 항목:**
- [ ] 이미지 데이터 반환
- [ ] 올바른 Content-Type

---

### TC-API-FILE-002: 존재하지 않는 이미지 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-FILE-002 |
| **테스트명** | 없는 페이지 이미지 조회 |
| **우선순위** | Medium |

**예상 결과:**
- 상태 코드: 404 Not Found

---

## 4. 설정 API (`/settings`)

### TC-API-SET-001: 설정 조회

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-SET-001 |
| **테스트명** | 시스템 설정 조회 |
| **우선순위** | Medium |

**요청:**
```bash
curl "http://localhost:8000/api/v1/settings"
```

**예상 결과:**
- 상태 코드: 200 OK
- 설정 값 반환

**검증 항목:**
- [ ] VLM 설정 포함
- [ ] OCR 설정 포함
- [ ] 일반 설정 포함

---

### TC-API-SET-002: 설정 수정

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-SET-002 |
| **테스트명** | 시스템 설정 수정 |
| **우선순위** | Medium |

**요청:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/settings" \
  -H "Content-Type: application/json" \
  -d '{"ocr_default_mode": "accurate"}'
```

**검증 항목:**
- [ ] 설정 값 변경 확인
- [ ] DB에 저장 확인

---

### TC-API-SET-003: VLM 연결 테스트

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-SET-003 |
| **테스트명** | VLM 서버 연결 테스트 |
| **우선순위** | High |

**요청:**
```bash
curl -X POST "http://localhost:8000/api/v1/settings/vlm/test" \
  -H "Content-Type: application/json" \
  -d '{"api_base": "http://chandra-vllm:8000/v1"}'
```

**예상 결과:**
- 상태 코드: 200 OK
- `connected: true` 또는 `connected: false`

**검증 항목:**
- [ ] 연결 상태 반환
- [ ] 모델 정보 반환 (연결 시)

---

## 5. 에러 처리 테스트

### TC-API-ERR-001: 잘못된 JSON 형식

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-ERR-001 |
| **테스트명** | 유효하지 않은 JSON 요청 |
| **우선순위** | Medium |

**요청:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/documents/1" \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
```

**예상 결과:**
- 상태 코드: 422 Unprocessable Entity

---

### TC-API-ERR-002: 필수 필드 누락

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-ERR-002 |
| **테스트명** | 필수 필드 없이 요청 |
| **우선순위** | Medium |

**요청:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -F "title=테스트"
# file 필드 누락
```

**예상 결과:**
- 상태 코드: 422 Unprocessable Entity
- 누락 필드 명시

---

### TC-API-ERR-003: 대용량 파일 업로드

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-ERR-003 |
| **테스트명** | 파일 크기 제한 테스트 |
| **우선순위** | Low |

**테스트 절차:**
1. 100MB 이상 파일 준비
2. 업로드 시도

**예상 결과:**
- 적절한 에러 메시지 또는 처리

---

## 6. CORS 테스트

### TC-API-CORS-001: CORS 헤더 확인

| 항목 | 내용 |
|------|------|
| **테스트 ID** | TC-API-CORS-001 |
| **테스트명** | CORS 헤더 검증 |
| **우선순위** | High |

**요청:**
```bash
curl -I -H "Origin: http://192.168.1.81:3000" \
  "http://localhost:8000/api/v1/documents"
```

**예상 결과:**
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: *`

**검증 항목:**
- [ ] CORS 헤더 존재
- [ ] 모든 오리진 허용

---

## 7. 테스트 자동화 스크립트

### pytest 테스트 예시

```python
# tests/test_api_documents.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_upload_document():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        with open("test.pdf", "rb") as f:
            response = await ac.post(
                "/api/v1/documents",
                files={"file": ("test.pdf", f, "application/pdf")},
                data={"title": "Test Document", "ocr_mode": "fast"}
            )
    assert response.status_code == 201
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_list_documents():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/documents")
    assert response.status_code == 200
    assert "items" in response.json()

@pytest.mark.asyncio
async def test_get_document_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/documents/99999")
    assert response.status_code == 404
```

---

## 8. 테스트 결과 템플릿

| 테스트 ID | 테스트명 | 결과 | 비고 |
|-----------|----------|------|------|
| TC-API-DOC-001 | PDF 문서 업로드 | PASS/FAIL | |
| TC-API-DOC-002 | PNG 이미지 업로드 | PASS/FAIL | |
| ... | ... | ... | ... |
