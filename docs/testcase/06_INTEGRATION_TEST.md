# 통합 및 E2E 테스트 케이스

## 1. 개요

시스템 전체 통합 및 End-to-End 테스트 케이스입니다. 모듈 간 상호작용과 전체 워크플로우를 검증합니다.

---

## 2. 시스템 통합 테스트

### TC-INT-SYS-001: 전체 서비스 헬스체크

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-SYS-001 |
| 테스트명 | 전체 서비스 상태 확인 |
| 우선순위 | Critical |
| 사전조건 | docker-compose up 완료 |

**테스트 절차:**
```bash
# 모든 컨테이너 상태 확인
docker compose ps

# 각 서비스 헬스체크
curl -s http://localhost:3000          # Frontend
curl -s http://localhost:8000/api/v1/  # Backend
curl -s http://localhost:9000/minio/health/live  # MinIO
docker exec pbt_vlm_ocr-postgres-1 pg_isready    # PostgreSQL
docker exec pbt_vlm_ocr-redis-1 redis-cli ping   # Redis
curl -s http://localhost:8080/health   # Chandra-VLLM
```

**예상 결과:**
- 모든 컨테이너 상태: Up
- 각 서비스 응답 정상

---

### TC-INT-SYS-002: 서비스 간 네트워크 연결

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-SYS-002 |
| 테스트명 | Docker 네트워크 내 서비스 간 통신 |
| 우선순위 | Critical |
| 사전조건 | pbt-network 생성됨 |

**테스트 절차:**
```bash
# Backend에서 다른 서비스 접근
docker exec pbt_vlm_ocr-backend-1 python -c "
import httpx
import redis

# PostgreSQL
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@postgres:5432/pbt_ocr')
print('PostgreSQL:', engine.execute('SELECT 1').fetchone())

# Redis
r = redis.from_url('redis://redis:6379/0')
print('Redis:', r.ping())

# MinIO
resp = httpx.get('http://minio:9000/minio/health/live')
print('MinIO:', resp.status_code)
"
```

**예상 결과:**
- 모든 서비스 간 통신 정상
- DNS 해석 정상 (서비스명으로 접근)

---

### TC-INT-SYS-003: 서비스 재시작 복구

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-SYS-003 |
| 테스트명 | 개별 서비스 재시작 후 복구 |
| 우선순위 | High |
| 사전조건 | 정상 운영 상태 |

**테스트 절차:**
```bash
# 1. Backend 재시작
docker restart pbt_vlm_ocr-backend-1
sleep 10
curl http://localhost:8000/api/v1/documents/

# 2. Worker 재시작
docker restart pbt_vlm_ocr-worker-fast-ocr-1
sleep 5
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN fast_ocr

# 3. Database 재시작 (주의: 데이터 보존 확인)
docker restart pbt_vlm_ocr-postgres-1
sleep 10
curl http://localhost:8000/api/v1/documents/
```

**예상 결과:**
- 각 서비스 재시작 후 정상 복구
- 데이터 손실 없음
- 연결 자동 재수립

---

## 3. 문서 업로드 → OCR 통합 테스트

### TC-INT-UPLOAD-001: 업로드 → 기본 OCR 플로우

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-UPLOAD-001 |
| 테스트명 | 문서 업로드 후 기본 OCR 처리 |
| 우선순위 | Critical |
| 사전조건 | 모든 서비스 정상 |

**테스트 절차:**
```bash
# 1. 문서 업로드
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=FAST")
DOC_ID=$(echo $RESPONSE | jq -r '.id')
echo "Document ID: $DOC_ID"

# 2. 상태 확인 (폴링)
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.status')
  echo "[$i] Status: $STATUS"
  if [ "$STATUS" == "completed" ]; then
    break
  fi
  sleep 2
done

# 3. 결과 확인
curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq '{
  status: .status,
  confidence: .confidence,
  page_count: .page_count,
  processing_time: .processing_time
}'
```

**예상 결과:**
- 업로드 성공 (HTTP 200/201)
- 상태 변화: pending → processing → completed
- OCR 결과 생성 (pages, blocks)

---

### TC-INT-UPLOAD-002: 업로드 → 고급 OCR 플로우

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-UPLOAD-002 |
| 테스트명 | 문서 업로드 후 고급 OCR 처리 |
| 우선순위 | Critical |
| 사전조건 | worker-accurate-ocr 실행 중 |

**테스트 절차:**
```bash
curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=ACCURATE"
```

**검증 포인트:**
- accurate_ocr 큐에 작업 추가
- PaddleOCR 처리
- 신뢰도 >= FAST 모드

---

### TC-INT-UPLOAD-003: 업로드 → 프리미엄 OCR 플로우

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-UPLOAD-003 |
| 테스트명 | 문서 업로드 후 프리미엄 OCR 처리 |
| 우선순위 | Critical |
| 사전조건 | chandra-vllm healthy, worker-precision-ocr 실행 중 |

**테스트 절차:**
```bash
# GPU 모니터링 시작
nvidia-smi dmon -s u -d 1 > /tmp/gpu_log.txt &
GPU_PID=$!

# 업로드 및 처리
curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=PRECISION"

# GPU 모니터링 종료
sleep 60
kill $GPU_PID

# GPU 사용률 확인
cat /tmp/gpu_log.txt
```

**예상 결과:**
- precision_ocr 큐에 작업 추가
- GPU 사용률 증가
- VLM 기반 OCR 결과

---

## 4. 데이터 일관성 테스트

### TC-INT-DATA-001: 업로드 데이터 일관성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-DATA-001 |
| 테스트명 | 업로드 시 DB-Storage 데이터 일관성 |
| 우선순위 | Critical |
| 사전조건 | 문서 업로드 완료 |

**테스트 절차:**
```bash
# 1. DB 레코드 확인
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT id, original_filename, storage_path FROM documents WHERE id = $DOC_ID;
"

# 2. MinIO 파일 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/$DOC_ID/
```

**예상 결과:**
- DB storage_path와 MinIO 파일 경로 일치
- 파일 크기 일치

---

### TC-INT-DATA-002: OCR 처리 후 데이터 일관성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-DATA-002 |
| 테스트명 | OCR 처리 후 DB-Storage 일관성 |
| 우선순위 | Critical |
| 사전조건 | OCR 처리 완료 |

**테스트 절차:**
```sql
-- 페이지 수 확인
SELECT
  d.page_count as doc_page_count,
  (SELECT COUNT(*) FROM pages WHERE document_id = d.id) as actual_pages
FROM documents d WHERE id = $DOC_ID;

-- 페이지별 이미지 확인
SELECT id, page_no, image_path FROM pages WHERE document_id = $DOC_ID;
```

```bash
# MinIO에서 페이지 이미지 확인
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/$DOC_ID/pages/
```

**예상 결과:**
- page_count = 실제 pages 레코드 수
- 각 페이지별 이미지 파일 존재

---

### TC-INT-DATA-003: 삭제 시 데이터 정리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-DATA-003 |
| 테스트명 | 문서 삭제 시 전체 데이터 정리 |
| 우선순위 | Critical |
| 사전조건 | 삭제할 문서 존재 |

**테스트 절차:**
```bash
# 삭제 전 확인
echo "=== Before Delete ==="
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT COUNT(*) FROM pages WHERE document_id = $DOC_ID;
"
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/$DOC_ID/ --recursive

# 삭제 실행
curl -X DELETE http://localhost:8000/api/v1/documents/$DOC_ID

# 삭제 후 확인
echo "=== After Delete ==="
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT COUNT(*) FROM documents WHERE id = $DOC_ID;
SELECT COUNT(*) FROM pages WHERE document_id = $DOC_ID;
"
docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/$DOC_ID/ --recursive
```

**예상 결과:**
- documents 레코드 삭제
- pages, blocks 레코드 cascade 삭제
- MinIO 파일 모두 삭제

---

## 5. 동시성 테스트

### TC-INT-CONC-001: 동시 문서 업로드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-CONC-001 |
| 테스트명 | 10개 문서 동시 업로드 |
| 우선순위 | High |
| 사전조건 | 테스트 파일 10개 준비 |

**테스트 절차:**
```bash
# 10개 동시 업로드
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/sample.pdf" \
    -F "ocr_mode=FAST" &
done
wait

# 결과 확인
curl -s http://localhost:8000/api/v1/documents/ | jq '.total'
```

**예상 결과:**
- 모든 업로드 성공
- 데이터 무결성 유지
- 경쟁 조건 없음

---

### TC-INT-CONC-002: 동시 OCR 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-CONC-002 |
| 테스트명 | 다중 OCR 작업 동시 처리 |
| 우선순위 | High |
| 사전조건 | Worker 동시성 설정 확인 |

**테스트 절차:**
```bash
# 5개 FAST OCR 동시 요청
for i in {1..5}; do
  curl -s -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/sample.pdf" \
    -F "ocr_mode=FAST" &
done
wait

# 큐 상태 확인
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN fast_ocr

# Worker 처리 모니터링
docker logs pbt_vlm_ocr-worker-fast-ocr-1 --tail 50
```

**예상 결과:**
- 4개 동시 처리 (concurrency=4)
- 나머지 큐 대기
- 모든 작업 완료

---

### TC-INT-CONC-003: 읽기/쓰기 동시 접근

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-CONC-003 |
| 테스트명 | 동시 읽기/쓰기 작업 |
| 우선순위 | Medium |
| 사전조건 | 문서 존재 |

**테스트 절차:**
```bash
# 동시에 읽기와 쓰기 수행
(
  # 읽기 작업 (반복)
  for i in {1..20}; do
    curl -s http://localhost:8000/api/v1/documents/ > /dev/null
  done
) &

(
  # 쓰기 작업 (업로드)
  for i in {1..5}; do
    curl -s -X POST http://localhost:8000/api/v1/documents/ \
      -F "file=@/data/sample.pdf" > /dev/null
  done
) &

wait
```

**예상 결과:**
- 모든 요청 정상 처리
- 데이터 일관성 유지

---

## 6. 장애 복구 테스트

### TC-INT-FAIL-001: Worker 장애 시 작업 복구

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-FAIL-001 |
| 테스트명 | OCR Worker 장애 시 작업 재시도 |
| 우선순위 | Critical |
| 사전조건 | OCR 작업 진행 중 |

**테스트 절차:**
```bash
# 1. OCR 작업 시작
curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/sample.pdf" \
  -F "ocr_mode=FAST"

# 2. Worker 강제 종료
docker kill pbt_vlm_ocr-worker-fast-ocr-1

# 3. 큐 상태 확인 (작업 남아있어야 함)
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN fast_ocr

# 4. Worker 재시작
docker start pbt_vlm_ocr-worker-fast-ocr-1

# 5. 작업 재처리 확인
sleep 30
curl -s http://localhost:8000/api/v1/documents/ | jq '.items[-1].status'
```

**예상 결과:**
- 작업 큐에 유지
- Worker 재시작 후 처리 재개
- 최종 완료

---

### TC-INT-FAIL-002: Database 연결 장애 복구

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-FAIL-002 |
| 테스트명 | PostgreSQL 일시 중단 후 복구 |
| 우선순위 | Critical |
| 사전조건 | 정상 운영 상태 |

**테스트 절차:**
```bash
# 1. PostgreSQL 중지
docker stop pbt_vlm_ocr-postgres-1

# 2. API 요청 (에러 발생 예상)
curl http://localhost:8000/api/v1/documents/

# 3. PostgreSQL 재시작
docker start pbt_vlm_ocr-postgres-1
sleep 10

# 4. 연결 복구 확인
curl http://localhost:8000/api/v1/documents/
```

**예상 결과:**
- 중지 시: 503 에러 또는 연결 에러
- 재시작 후: 자동 재연결
- 데이터 손실 없음

---

### TC-INT-FAIL-003: VLM 서비스 장애 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-FAIL-003 |
| 테스트명 | Chandra-VLLM 장애 시 PRECISION OCR 처리 |
| 우선순위 | High |
| 사전조건 | PRECISION OCR 요청 |

**테스트 절차:**
```bash
# 1. PRECISION OCR 요청
DOC_ID=$(curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/sample.pdf" \
  -F "ocr_mode=PRECISION" | jq -r '.id')

# 2. VLM 서비스 중지
docker stop pbt_vlm_ocr-chandra-vllm-1

# 3. 작업 상태 확인
sleep 30
curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq '.status'

# 4. VLM 서비스 재시작
docker start pbt_vlm_ocr-chandra-vllm-1
sleep 120  # 모델 로딩 대기

# 5. 작업 재시도 또는 수동 재처리
```

**예상 결과:**
- 타임아웃 후 실패 상태 또는 재시도
- 에러 메시지 명확
- VLM 복구 후 재처리 가능

---

## 7. E2E 사용자 시나리오 테스트

### TC-INT-E2E-001: 완전한 문서 처리 워크플로우

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-E2E-001 |
| 테스트명 | 업로드 → OCR → 검토 → 수정 → 저장 |
| 우선순위 | Critical |
| 사전조건 | 모든 서비스 정상 |

**테스트 시나리오:**
```
1. 사용자가 웹 브라우저로 http://localhost:3000 접속
2. PDF 파일 드래그 앤 드롭으로 업로드
3. OCR 모드 "고급(CPU)" 선택
4. 업로드 완료 메시지 확인
5. "문서 목록" 페이지에서 업로드된 문서 확인
6. 문서 클릭하여 상세 페이지 이동
7. OCR 처리 완료까지 대기 (상태 변화 관찰)
8. 이미지 뷰어에서 문서 확인
9. "블록 표시" 활성화하여 OCR 블록 확인
10. 특정 블록 클릭하여 텍스트 확인
11. 텍스트 편집기에서 오류 수정
12. 저장 버튼 클릭
13. 저장 완료 확인
```

**예상 결과:**
- 모든 단계 정상 수행
- 각 단계별 적절한 피드백
- 수정된 데이터 영구 저장

---

### TC-INT-E2E-002: 다중 문서 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-E2E-002 |
| 테스트명 | 여러 문서 순차/병렬 처리 |
| 우선순위 | High |
| 사전조건 | 테스트 문서 5개 준비 |

**테스트 시나리오:**
```
1. 5개 PDF 파일 순차 업로드
   - 문서1: FAST 모드
   - 문서2: FAST 모드
   - 문서3: ACCURATE 모드
   - 문서4: ACCURATE 모드
   - 문서5: PRECISION 모드
2. 큐 페이지에서 처리 상태 확인
3. 각 문서의 처리 완료 확인
4. 처리 시간 비교
```

**예상 결과:**
- 각 모드별 큐로 분배
- 동시 처리 (Worker별 concurrency)
- 모든 문서 처리 완료

---

### TC-INT-E2E-003: 대용량 문서 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-E2E-003 |
| 테스트명 | 50페이지 이상 대용량 문서 처리 |
| 우선순위 | Medium |
| 사전조건 | 50페이지 PDF 준비 |

**테스트 절차:**
1. 50페이지 PDF 업로드
2. OCR 처리 시작
3. 진행률 모니터링
4. 전체 처리 완료 확인
5. 각 페이지 OCR 결과 확인

**예상 결과:**
- 메모리 오버플로우 없음
- 페이지별 순차 처리
- 전체 완료 시간 측정

---

## 8. API 통합 테스트

### TC-INT-API-001: 문서 API CRUD 전체 플로우

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-API-001 |
| 테스트명 | 문서 API CRUD 통합 테스트 |
| 우선순위 | Critical |
| 사전조건 | - |

**테스트 절차:**
```bash
# 1. CREATE
echo "=== CREATE ==="
DOC_ID=$(curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/sample.pdf" | jq -r '.id')
echo "Created: $DOC_ID"

# 2. READ (단일)
echo "=== READ ==="
curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq '.status'

# 3. READ (목록)
echo "=== LIST ==="
curl -s http://localhost:8000/api/v1/documents/ | jq '.total'

# 4. UPDATE (OCR 재처리)
echo "=== UPDATE (Re-OCR) ==="
curl -s -X POST http://localhost:8000/api/v1/documents/$DOC_ID/ocr \
  -H "Content-Type: application/json" \
  -d '{"ocr_mode": "ACCURATE"}'

# 5. DELETE
echo "=== DELETE ==="
curl -s -X DELETE http://localhost:8000/api/v1/documents/$DOC_ID
curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq '.detail'
```

**예상 결과:**
- 각 CRUD 작업 성공
- 적절한 HTTP 상태 코드

---

### TC-INT-API-002: 파일 API 통합

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-API-002 |
| 테스트명 | 파일 다운로드/이미지 프록시 |
| 우선순위 | High |
| 사전조건 | OCR 완료된 문서 존재 |

**테스트 절차:**
```bash
# 원본 다운로드
curl -o original.pdf http://localhost:8000/api/v1/files/documents/$DOC_ID/download
ls -la original.pdf

# 페이지 이미지 다운로드
curl -o page1.png http://localhost:8000/api/v1/files/documents/$DOC_ID/pages/1/image
file page1.png
```

**예상 결과:**
- 원본 PDF 정상 다운로드
- 페이지 이미지 PNG 형식

---

## 9. 모니터링 테스트

### TC-INT-MON-001: 처리 상태 실시간 추적

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-MON-001 |
| 테스트명 | OCR 처리 상태 실시간 추적 |
| 우선순위 | Medium |
| 사전조건 | 진행 중인 OCR 작업 |

**테스트 절차:**
```bash
# 상태 변화 추적
DOC_ID=1
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.status')
  PROGRESS=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.progress // 0')
  echo "[$(date +%H:%M:%S)] Status: $STATUS, Progress: $PROGRESS%"

  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    break
  fi
  sleep 2
done
```

**예상 결과:**
- 상태 변화 추적 가능
- pending → processing → completed

---

### TC-INT-MON-002: 큐 상태 모니터링

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-MON-002 |
| 테스트명 | Celery 큐 상태 API 확인 |
| 우선순위 | Medium |
| 사전조건 | - |

**테스트 절차:**
```bash
# 큐 상태 API 호출
curl -s http://localhost:8000/api/v1/queue/status | jq

# Redis 직접 확인
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN fast_ocr
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN accurate_ocr
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN precision_ocr
```

**예상 결과:**
- 각 큐별 대기 작업 수
- 처리 중인 작업 정보

---

## 10. 외부 접근 테스트

### TC-INT-EXT-001: 외부 IP로 서비스 접근

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-INT-EXT-001 |
| 테스트명 | 외부 IP를 통한 서비스 접근 |
| 우선순위 | High |
| 사전조건 | 외부 접근 가능한 네트워크 |

**테스트 절차:**
```bash
# 호스트 IP 확인
HOST_IP=$(hostname -I | awk '{print $1}')
echo "Host IP: $HOST_IP"

# 외부 접근 테스트
curl http://$HOST_IP:3000          # Frontend
curl http://$HOST_IP:8000/api/v1/  # Backend
```

**예상 결과:**
- CORS 에러 없음
- API 정상 응답
- 동적 URL 적용 확인

---

## 11. 자동화 테스트 스크립트

```bash
#!/bin/bash
# 통합 테스트 실행 스크립트

set -e

echo "=== PBT VLM OCR 통합 테스트 시작 ==="

# 테스트 결과 저장
RESULTS=()

# 1. 서비스 헬스체크
echo "[1/8] 서비스 헬스체크..."
if docker compose ps | grep -q "Up"; then
  RESULTS+=("헬스체크: PASS")
else
  RESULTS+=("헬스체크: FAIL")
fi

# 2. 문서 업로드 테스트
echo "[2/8] 문서 업로드 테스트..."
RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/upload_response.json \
  -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=FAST")
if [ "$RESPONSE" == "200" ] || [ "$RESPONSE" == "201" ]; then
  DOC_ID=$(cat /tmp/upload_response.json | jq -r '.id')
  RESULTS+=("업로드: PASS (ID: $DOC_ID)")
else
  RESULTS+=("업로드: FAIL (HTTP $RESPONSE)")
fi

# 3. OCR 처리 대기
echo "[3/8] OCR 처리 대기..."
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.status')
  if [ "$STATUS" == "completed" ]; then
    RESULTS+=("OCR 처리: PASS")
    break
  elif [ "$STATUS" == "failed" ]; then
    RESULTS+=("OCR 처리: FAIL")
    break
  fi
  sleep 2
done

# 4. DB 데이터 확인
echo "[4/8] DB 데이터 확인..."
PAGE_COUNT=$(docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -t -c \
  "SELECT COUNT(*) FROM pages WHERE document_id = $DOC_ID;")
if [ "$PAGE_COUNT" -gt 0 ]; then
  RESULTS+=("DB 데이터: PASS ($PAGE_COUNT pages)")
else
  RESULTS+=("DB 데이터: FAIL")
fi

# 5. Storage 파일 확인
echo "[5/8] Storage 파일 확인..."
FILE_COUNT=$(docker exec pbt_vlm_ocr-minio-1 mc ls local/pbt-ocr-documents/documents/$DOC_ID/ --recursive | wc -l)
if [ "$FILE_COUNT" -gt 0 ]; then
  RESULTS+=("Storage: PASS ($FILE_COUNT files)")
else
  RESULTS+=("Storage: FAIL")
fi

# 6. 이미지 다운로드 테스트
echo "[6/8] 이미지 다운로드 테스트..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
  http://localhost:8000/api/v1/files/documents/$DOC_ID/pages/1/image)
if [ "$HTTP_CODE" == "200" ]; then
  RESULTS+=("이미지 다운로드: PASS")
else
  RESULTS+=("이미지 다운로드: FAIL")
fi

# 7. Frontend 접근 테스트
echo "[7/8] Frontend 접근 테스트..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:3000)
if [ "$HTTP_CODE" == "200" ]; then
  RESULTS+=("Frontend: PASS")
else
  RESULTS+=("Frontend: FAIL")
fi

# 8. 문서 삭제 테스트
echo "[8/8] 문서 삭제 테스트..."
curl -s -X DELETE http://localhost:8000/api/v1/documents/$DOC_ID
DELETED=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.detail')
if [[ "$DELETED" == *"not found"* ]]; then
  RESULTS+=("삭제: PASS")
else
  RESULTS+=("삭제: FAIL")
fi

# 결과 출력
echo ""
echo "=== 테스트 결과 요약 ==="
for result in "${RESULTS[@]}"; do
  echo "  - $result"
done
echo "========================"
```

---

## 12. Playwright E2E 테스트

```typescript
// tests/e2e/integration.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Integration Tests', () => {

  test('complete document workflow', async ({ page }) => {
    // 1. 메인 페이지 접속
    await page.goto('/');

    // 2. 파일 업로드
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles('./test-data/sample.pdf');

    // 3. OCR 모드 선택
    await page.click('text=기본(CPU)');

    // 4. 업로드
    await page.click('button:has-text("업로드")');

    // 5. 성공 메시지 대기
    await expect(page.locator('text=업로드 완료')).toBeVisible({ timeout: 10000 });

    // 6. 문서 목록으로 이동
    await page.goto('/documents');

    // 7. 업로드된 문서 확인
    await expect(page.locator('.document-card').first()).toBeVisible();

    // 8. 문서 상세 페이지로 이동
    await page.click('.document-card:first-child');

    // 9. OCR 완료 대기
    await expect(page.locator('text=completed')).toBeVisible({ timeout: 60000 });

    // 10. 이미지 뷰어 확인
    await expect(page.locator('.page-viewer img')).toBeVisible();

    // 11. 텍스트 편집기 확인
    await expect(page.locator('.text-editor')).toContainText(/./);
  });
});
```
