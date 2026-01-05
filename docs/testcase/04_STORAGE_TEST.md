# Storage (MinIO) 테스트 케이스

## 1. 개요

MinIO 오브젝트 스토리지에 대한 테스트 케이스입니다. 파일 저장, 조회, 삭제 및 접근 제어를 검증합니다.

---

## 2. 연결 테스트

### TC-STG-CONN-001: MinIO 서버 연결 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-CONN-001 |
| 테스트명 | MinIO 서버 연결 확인 |
| 우선순위 | Critical |
| 사전조건 | minio 컨테이너 실행 중 |

**테스트 절차:**
```bash
# MinIO 헬스체크
curl -I http://localhost:9000/minio/health/live

# mc 클라이언트로 연결 테스트
docker exec pbt_vlm_ocr-minio-1 mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec pbt_vlm_ocr-minio-1 mc admin info local
```

**예상 결과:**
- 200 OK 응답
- 서버 정보 정상 출력

---

### TC-STG-CONN-002: Backend에서 MinIO 연결

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-CONN-002 |
| 테스트명 | Backend 서비스에서 MinIO 연결 |
| 우선순위 | Critical |
| 사전조건 | Backend 서비스 실행 중 |

**테스트 절차:**
```bash
docker exec pbt_vlm_ocr-backend-1 python -c "
from app.core.storage import storage_client
print('MinIO endpoint:', storage_client.endpoint)
print('Bucket exists:', storage_client.bucket_exists('pbt-ocr-documents'))
"
```

**예상 결과:**
- 연결 성공
- 버킷 존재 확인

---

## 3. 버킷 테스트

### TC-STG-BKT-001: 기본 버킷 존재 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-BKT-001 |
| 테스트명 | pbt-ocr-documents 버킷 존재 확인 |
| 우선순위 | Critical |
| 사전조건 | MinIO 초기화 완료 |

**테스트 절차:**
```bash
# 버킷 목록 조회
curl http://localhost:9000 -u minioadmin:minioadmin

# mc 클라이언트 사용
docker exec pbt_vlm_ocr-minio-1 mc ls local/
```

**예상 결과:**
- pbt-ocr-documents 버킷 존재

---

### TC-STG-BKT-002: 버킷 자동 생성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-BKT-002 |
| 테스트명 | Backend 시작 시 버킷 자동 생성 |
| 우선순위 | High |
| 사전조건 | 버킷 미존재 상태 |

**테스트 절차:**
```bash
# 버킷 삭제
docker exec pbt_vlm_ocr-minio-1 mc rb local/pbt-ocr-documents --force

# Backend 재시작
docker restart pbt_vlm_ocr-backend-1

# 버킷 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/
```

**예상 결과:**
- Backend 시작 시 버킷 자동 생성
- pbt-ocr-documents 버킷 존재

---

## 4. 파일 업로드 테스트

### TC-STG-UP-001: PDF 파일 업로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-UP-001 |
| 테스트명 | PDF 파일 MinIO 업로드 |
| 우선순위 | Critical |
| 사전조건 | 버킷 존재, 테스트 파일 준비 |

**테스트 절차:**
```bash
# API를 통한 파일 업로드
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf"

# MinIO에서 파일 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/ --recursive
```

**예상 결과:**
- 업로드 성공
- MinIO에 파일 저장됨
- 경로: `documents/{document_id}/original.pdf`

---

### TC-STG-UP-002: 이미지 파일 업로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-UP-002 |
| 테스트명 | PNG/JPG 이미지 MinIO 업로드 |
| 우선순위 | High |
| 사전조건 | 버킷 존재 |

**테스트 절차:**
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/sample_image.png"
```

**예상 결과:**
- 이미지 업로드 성공
- MIME 타입 정확히 저장

---

### TC-STG-UP-003: 대용량 파일 업로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-UP-003 |
| 테스트명 | 50MB 이상 대용량 파일 업로드 |
| 우선순위 | Medium |
| 사전조건 | 대용량 테스트 파일 준비 |

**테스트 절차:**
```bash
# 대용량 파일 생성 (테스트용)
dd if=/dev/zero of=/tmp/large_file.pdf bs=1M count=50

# 업로드
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/tmp/large_file.pdf"
```

**예상 결과:**
- 멀티파트 업로드 사용
- 업로드 시간 < 30초 (네트워크 환경에 따라)

---

### TC-STG-UP-004: 페이지 이미지 저장

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-UP-004 |
| 테스트명 | OCR 처리 시 페이지 이미지 저장 |
| 우선순위 | High |
| 사전조건 | OCR 처리 완료된 문서 존재 |

**테스트 절차:**
```bash
# OCR 처리 후 페이지 이미지 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/{id}/pages/
```

**예상 결과:**
- 각 페이지별 이미지 파일 존재
- 경로: `documents/{document_id}/pages/{page_no}.png`

---

## 5. 파일 다운로드 테스트

### TC-STG-DOWN-001: 원본 파일 다운로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-DOWN-001 |
| 테스트명 | 원본 PDF 파일 다운로드 |
| 우선순위 | Critical |
| 사전조건 | 업로드된 문서 존재 |

**테스트 절차:**
```bash
# API를 통한 다운로드
curl -O http://localhost:8000/api/v1/files/documents/{document_id}/download

# 파일 크기 확인
ls -la downloaded_file.pdf
```

**예상 결과:**
- 파일 정상 다운로드
- 원본 파일과 동일한 크기

---

### TC-STG-DOWN-002: 페이지 이미지 다운로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-DOWN-002 |
| 테스트명 | 페이지 이미지 다운로드 (프록시) |
| 우선순위 | High |
| 사전조건 | OCR 처리된 문서 존재 |

**테스트 절차:**
```bash
# 프록시 API를 통한 이미지 다운로드
curl -O http://localhost:8000/api/v1/files/documents/{document_id}/pages/{page_no}/image
```

**예상 결과:**
- PNG 이미지 정상 다운로드
- Content-Type: image/png

---

### TC-STG-DOWN-003: Presigned URL 생성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-DOWN-003 |
| 테스트명 | MinIO Presigned URL 생성 및 접근 |
| 우선순위 | Medium |
| 사전조건 | 파일 존재 |

**테스트 절차:**
```python
# Backend에서 Presigned URL 생성
from app.core.storage import storage_client

url = storage_client.presigned_get_object(
    bucket_name="pbt-ocr-documents",
    object_name="documents/1/original.pdf",
    expires=3600
)
print(url)
```

**예상 결과:**
- 유효한 Presigned URL 생성
- 1시간 동안 접근 가능

---

## 6. 파일 삭제 테스트

### TC-STG-DEL-001: 단일 파일 삭제

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-DEL-001 |
| 테스트명 | 단일 파일 삭제 |
| 우선순위 | High |
| 사전조건 | 삭제할 파일 존재 |

**테스트 절차:**
```bash
# API를 통한 문서 삭제
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}

# MinIO에서 파일 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/{document_id}/
```

**예상 결과:**
- API 응답: 204 No Content
- MinIO에서 파일 삭제됨

---

### TC-STG-DEL-002: 문서 관련 모든 파일 삭제

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-DEL-002 |
| 테스트명 | 문서 삭제 시 연관 파일 전체 삭제 |
| 우선순위 | Critical |
| 사전조건 | 원본 + 페이지 이미지 존재 |

**테스트 절차:**
```bash
# 삭제 전 파일 목록
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/{document_id}/ --recursive

# 문서 삭제
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}

# 삭제 후 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/{document_id}/ --recursive
```

**예상 결과:**
- 원본 파일 삭제
- 모든 페이지 이미지 삭제
- 빈 폴더도 정리

---

## 7. 파일 메타데이터 테스트

### TC-STG-META-001: 파일 메타데이터 저장

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-META-001 |
| 테스트명 | 파일 업로드 시 메타데이터 저장 |
| 우선순위 | Medium |
| 사전조건 | 파일 업로드 |

**테스트 절차:**
```bash
# 파일 메타데이터 조회
docker exec pbt_vlm_ocr-minio-1 mc stat local/pbt-ocr-documents/documents/{id}/original.pdf
```

**예상 결과:**
- Content-Type 정확
- Size 정확
- ETag 존재
- Last-Modified 존재

---

### TC-STG-META-002: MIME 타입 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-META-002 |
| 테스트명 | 파일 MIME 타입 정확성 |
| 우선순위 | Medium |
| 사전조건 | 다양한 파일 형식 업로드 |

**테스트 케이스:**
| 파일 형식 | 예상 MIME 타입 |
|-----------|---------------|
| PDF | application/pdf |
| PNG | image/png |
| JPG | image/jpeg |
| TIFF | image/tiff |

---

## 8. 저장 경로 구조 테스트

### TC-STG-PATH-001: 문서 저장 경로 구조

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-PATH-001 |
| 테스트명 | 문서 저장 경로 구조 확인 |
| 우선순위 | High |
| 사전조건 | OCR 처리된 문서 존재 |

**예상 경로 구조:**
```
pbt-ocr-documents/
└── documents/
    └── {document_id}/
        ├── original.pdf          # 원본 파일
        └── pages/
            ├── 1.png             # 1페이지 이미지
            ├── 2.png             # 2페이지 이미지
            └── 3.png             # 3페이지 이미지
```

**테스트 절차:**
```bash
docker exec pbt_vlm_ocr-minio-1 mc tree local/pbt-ocr-documents/
```

---

## 9. 용량 및 성능 테스트

### TC-STG-PERF-001: 업로드 속도 측정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-PERF-001 |
| 테스트명 | 파일 업로드 속도 측정 |
| 우선순위 | High |
| 목표 | 10MB 파일 < 3초 |

**테스트 절차:**
```bash
# 10MB 파일 업로드 시간 측정
time curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/tmp/10mb_file.pdf"
```

**예상 결과:**
- 업로드 시간 < 3초
- 네트워크 병목 확인

---

### TC-STG-PERF-002: 다운로드 속도 측정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-PERF-002 |
| 테스트명 | 파일 다운로드 속도 측정 |
| 우선순위 | High |
| 목표 | 10MB 파일 < 2초 |

**테스트 절차:**
```bash
time curl -O http://localhost:8000/api/v1/files/documents/{id}/download
```

**예상 결과:**
- 다운로드 시간 < 2초

---

### TC-STG-PERF-003: 동시 업로드 성능

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-PERF-003 |
| 테스트명 | 10개 파일 동시 업로드 |
| 우선순위 | Medium |
| 목표 | 전체 완료 < 30초 |

**테스트 절차:**
```bash
# 10개 파일 동시 업로드
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/sample.pdf" &
done
wait
```

**예상 결과:**
- 모든 파일 업로드 성공
- 총 시간 < 30초

---

### TC-STG-PERF-004: 스토리지 용량 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-PERF-004 |
| 테스트명 | MinIO 스토리지 사용량 확인 |
| 우선순위 | Low |
| 사전조건 | 테스트 데이터 존재 |

**테스트 절차:**
```bash
# 버킷 사용량 확인
docker exec pbt_vlm_ocr-minio-1 mc du local/pbt-ocr-documents/
```

---

## 10. 에러 처리 테스트

### TC-STG-ERR-001: 존재하지 않는 파일 다운로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-ERR-001 |
| 테스트명 | 존재하지 않는 파일 다운로드 시도 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
curl -v http://localhost:8000/api/v1/files/documents/99999/download
```

**예상 결과:**
- HTTP 404 Not Found
- 적절한 에러 메시지

---

### TC-STG-ERR-002: 지원하지 않는 파일 형식 업로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-ERR-002 |
| 테스트명 | 지원하지 않는 파일 형식 업로드 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/tmp/test.exe"
```

**예상 결과:**
- HTTP 400 Bad Request
- 에러 메시지: "Unsupported file type"

---

### TC-STG-ERR-003: MinIO 연결 실패 시 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-ERR-003 |
| 테스트명 | MinIO 서비스 장애 시 에러 처리 |
| 우선순위 | Critical |
| 사전조건 | MinIO 중지 가능 |

**테스트 절차:**
```bash
# MinIO 중지
docker stop pbt_vlm_ocr-minio-1

# 파일 업로드 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/sample.pdf"

# MinIO 재시작
docker start pbt_vlm_ocr-minio-1
```

**예상 결과:**
- 적절한 에러 응답
- 시스템 크래시 없음

---

### TC-STG-ERR-004: 디스크 공간 부족 시 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-ERR-004 |
| 테스트명 | 스토리지 공간 부족 시 에러 처리 |
| 우선순위 | Medium |
| 사전조건 | 디스크 공간 제한 설정 |

**테스트 절차:**
- 디스크 할당량 제한 설정 후 대용량 파일 업로드 시도

**예상 결과:**
- 적절한 에러 메시지
- 부분 업로드 파일 정리

---

## 11. MinIO Console 테스트

### TC-STG-CONSOLE-001: MinIO Console 접속

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-CONSOLE-001 |
| 테스트명 | MinIO Console 웹 UI 접속 |
| 우선순위 | Low |
| 사전조건 | minio 컨테이너 실행 중 |

**테스트 절차:**
1. 브라우저에서 http://localhost:9001 접속
2. 로그인: minioadmin / minioadmin
3. 버킷 및 파일 목록 확인

**예상 결과:**
- 로그인 성공
- pbt-ocr-documents 버킷 표시
- 파일 목록 조회 가능

---

## 12. 데이터 일관성 테스트

### TC-STG-CONS-001: DB-Storage 동기화

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-CONS-001 |
| 테스트명 | DB 레코드와 Storage 파일 일관성 |
| 우선순위 | Critical |
| 사전조건 | 여러 문서 존재 |

**테스트 절차:**
```sql
-- DB에서 storage_path 조회
SELECT id, storage_path FROM documents;
```

```bash
# MinIO에서 실제 파일 존재 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/ --recursive
```

**예상 결과:**
- 모든 DB 레코드에 대응하는 파일 존재
- 고아 파일(DB에 없는 파일) 없음

---

### TC-STG-CONS-002: 문서 삭제 후 정리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-STG-CONS-002 |
| 테스트명 | 문서 삭제 시 Storage 파일 정리 |
| 우선순위 | Critical |
| 사전조건 | 삭제할 문서 존재 |

**테스트 절차:**
1. 문서 삭제 API 호출
2. DB 레코드 삭제 확인
3. MinIO 파일 삭제 확인

**예상 결과:**
- DB 레코드 삭제
- 원본 파일 삭제
- 페이지 이미지 모두 삭제

---

## 13. 자동화 테스트 스크립트

```bash
#!/bin/bash
# Storage (MinIO) 테스트 실행 스크립트

echo "=== Storage 테스트 시작 ==="

# 1. MinIO 연결 테스트
echo "[1/5] MinIO 연결 테스트..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live

# 2. 버킷 확인
echo "[2/5] 버킷 확인..."
docker exec pbt_vlm_ocr-minio-1 mc ls local/

# 3. 파일 업로드 테스트
echo "[3/5] 파일 업로드 테스트..."
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" | jq '.id'

# 4. 파일 목록 확인
echo "[4/5] 저장된 파일 목록..."
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/ --recursive | head -20

# 5. 용량 확인
echo "[5/5] 스토리지 사용량..."
docker exec pbt_vlm_ocr-minio-1 mc du local/pbt-ocr-documents/

echo "=== Storage 테스트 완료 ==="
```
