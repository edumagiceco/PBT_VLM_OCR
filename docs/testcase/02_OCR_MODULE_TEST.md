# OCR 모듈 테스트 케이스

## 1. 개요

OCR 처리 모듈에 대한 테스트 케이스입니다. 3가지 OCR 모드(기본/고급/프리미엄)의 기능 및 성능을 검증합니다.

---

## 2. 기본 OCR (Tesseract) 테스트

### TC-OCR-FAST-001: 기본 OCR 단일 페이지 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-FAST-001 |
| 테스트명 | 기본 OCR 단일 페이지 처리 |
| 우선순위 | High |
| 사전조건 | worker-fast-ocr 컨테이너 실행 중, Redis 연결 정상 |

**테스트 절차:**
1. PDF 문서(1페이지) 업로드
2. OCR 모드를 "FAST"로 선택
3. OCR 처리 요청
4. 처리 완료까지 대기

**예상 결과:**
- 처리 시간: 2초 이내
- 상태: "completed"
- 텍스트 추출 결과 존재
- 신뢰도 점수 반환

**검증 쿼리:**
```sql
SELECT status, ocr_mode, processing_time, confidence
FROM documents WHERE id = {document_id};

SELECT COUNT(*) FROM pages WHERE document_id = {document_id};
SELECT COUNT(*) FROM blocks WHERE page_id IN (SELECT id FROM pages WHERE document_id = {document_id});
```

---

### TC-OCR-FAST-002: 기본 OCR 다중 페이지 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-FAST-002 |
| 테스트명 | 기본 OCR 다중 페이지 처리 (3페이지) |
| 우선순위 | High |
| 사전조건 | worker-fast-ocr 컨테이너 실행 중 |

**테스트 절차:**
1. PDF 문서(3페이지) 업로드
2. OCR 모드를 "FAST"로 선택
3. OCR 처리 요청
4. 각 페이지 처리 상태 확인

**예상 결과:**
- 전체 처리 시간: 6초 이내 (페이지당 2초)
- 모든 페이지 텍스트 추출 완료
- 각 페이지별 신뢰도 점수 존재

---

### TC-OCR-FAST-003: 기본 OCR 이미지 파일 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-FAST-003 |
| 테스트명 | 기본 OCR PNG/JPG 이미지 처리 |
| 우선순위 | Medium |
| 사전조건 | worker-fast-ocr 컨테이너 실행 중 |

**테스트 절차:**
1. PNG 이미지 파일 업로드
2. OCR 모드를 "FAST"로 선택
3. OCR 처리 요청

**예상 결과:**
- 이미지 텍스트 추출 성공
- 단일 페이지로 처리
- 블록 좌표(bbox) 정보 포함

---

### TC-OCR-FAST-004: 기본 OCR 한글 문서 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-FAST-004 |
| 테스트명 | 기본 OCR 한글 문서 인식 |
| 우선순위 | High |
| 사전조건 | Tesseract 한글 언어팩 설치됨 |

**테스트 절차:**
1. 한글 문서(personnel_regulations.pdf) 업로드
2. OCR 모드를 "FAST"로 선택
3. OCR 처리 요청
4. 추출된 텍스트 확인

**예상 결과:**
- 한글 텍스트 정상 추출
- 특수문자, 숫자 정상 인식
- 문서 구조(제목, 본문) 구분

---

### TC-OCR-FAST-005: 기본 OCR 동시 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-FAST-005 |
| 테스트명 | 기본 OCR 4개 동시 처리 |
| 우선순위 | Medium |
| 사전조건 | worker-fast-ocr concurrency=4 설정 |

**테스트 절차:**
1. 4개의 PDF 문서 동시 업로드
2. 모든 문서에 FAST OCR 요청
3. 동시 처리 상태 확인

**예상 결과:**
- 4개 문서 병렬 처리
- 모든 문서 정상 완료
- 리소스 경합 없음

---

## 3. 고급 OCR (PaddleOCR) 테스트

### TC-OCR-ACC-001: 고급 OCR 단일 페이지 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ACC-001 |
| 테스트명 | 고급 OCR 단일 페이지 처리 |
| 우선순위 | High |
| 사전조건 | worker-accurate-ocr 컨테이너 실행 중, PaddleOCR 모델 로드됨 |

**테스트 절차:**
1. PDF 문서(1페이지) 업로드
2. OCR 모드를 "ACCURATE"로 선택
3. OCR 처리 요청
4. 처리 완료까지 대기

**예상 결과:**
- 처리 시간: 5초 이내
- 상태: "completed"
- 기본 OCR 대비 높은 신뢰도
- 텍스트 추출 결과 존재

**검증 방법:**
```bash
# Celery 작업 상태 확인
docker exec pbt_vlm_ocr-worker-accurate-ocr-1 celery -A app.core.celery_app inspect active

# Redis 큐 상태 확인
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN accurate_ocr
```

---

### TC-OCR-ACC-002: 고급 OCR 다중 페이지 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ACC-002 |
| 테스트명 | 고급 OCR 다중 페이지 처리 (3페이지) |
| 우선순위 | High |
| 사전조건 | worker-accurate-ocr 컨테이너 실행 중 |

**테스트 절차:**
1. PDF 문서(3페이지) 업로드
2. OCR 모드를 "ACCURATE"로 선택
3. OCR 처리 요청
4. 진행률 확인

**예상 결과:**
- 전체 처리 시간: 15초 이내
- 페이지별 순차 처리
- 진행률 정보 업데이트

---

### TC-OCR-ACC-003: 고급 OCR 신뢰도 비교

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ACC-003 |
| 테스트명 | 기본 OCR vs 고급 OCR 신뢰도 비교 |
| 우선순위 | High |
| 사전조건 | 동일 문서로 테스트 |

**테스트 절차:**
1. 동일 문서를 FAST 모드로 처리
2. 동일 문서를 ACCURATE 모드로 처리
3. 신뢰도 점수 비교

**예상 결과:**
- ACCURATE 모드 신뢰도 >= FAST 모드 신뢰도
- 저품질 스캔 문서에서 차이 더 큼

**비교 쿼리:**
```sql
SELECT d.id, d.original_filename, d.ocr_mode, d.confidence,
       (SELECT AVG(confidence) FROM pages WHERE document_id = d.id) as avg_page_confidence
FROM documents d
WHERE d.original_filename = 'test_document.pdf'
ORDER BY d.ocr_mode;
```

---

### TC-OCR-ACC-004: 고급 OCR 테이블 인식

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ACC-004 |
| 테스트명 | 고급 OCR 테이블 구조 인식 |
| 우선순위 | Medium |
| 사전조건 | 테이블 포함 문서 준비 |

**테스트 절차:**
1. 테이블이 포함된 PDF 업로드
2. ACCURATE 모드로 OCR 처리
3. 블록 타입 확인

**예상 결과:**
- block_type = 'table' 블록 생성
- 테이블 셀 텍스트 추출
- 테이블 구조 정보 포함

---

### TC-OCR-ACC-005: 고급 OCR PP-OCRv5 모델 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ACC-005 |
| 테스트명 | PaddleOCR PP-OCRv5 모델 사용 확인 |
| 우선순위 | Medium |
| 사전조건 | worker-accurate-ocr 로그 확인 가능 |

**테스트 절차:**
1. OCR 처리 요청
2. worker-accurate-ocr 로그 확인

**예상 결과:**
```
PP-OCRv5 모델 로드됨
Using PP-OCRv5 for text detection and recognition
```

**검증 명령:**
```bash
docker logs pbt_vlm_ocr-worker-accurate-ocr-1 2>&1 | grep -i "PP-OCR"
```

---

## 4. 프리미엄 OCR (VLM GPU) 테스트

### TC-OCR-PREC-001: 프리미엄 OCR 단일 페이지 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PREC-001 |
| 테스트명 | 프리미엄 OCR 단일 페이지 처리 |
| 우선순위 | Critical |
| 사전조건 | chandra-vllm 서비스 healthy, GPU 사용 가능 |

**테스트 절차:**
1. PDF 문서(1페이지) 업로드
2. OCR 모드를 "PRECISION"으로 선택
3. OCR 처리 요청
4. GPU 사용률 모니터링

**예상 결과:**
- 처리 시간: 10초 이내
- GPU 사용률 > 50%
- 최고 수준의 신뢰도
- 상태: "completed"

**GPU 모니터링:**
```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1
```

---

### TC-OCR-PREC-002: 프리미엄 OCR VLM API 연결 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PREC-002 |
| 테스트명 | Chandra-VLLM API 연결 확인 |
| 우선순위 | Critical |
| 사전조건 | chandra-vllm 컨테이너 실행 중 |

**테스트 절차:**
1. VLM API 헬스체크 호출
2. 모델 목록 조회
3. 간단한 텍스트 생성 테스트

**API 테스트:**
```bash
# 헬스체크
curl http://localhost:8080/health

# 모델 목록
curl http://localhost:8080/v1/models

# 테스트 요청
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-vl",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'
```

**예상 결과:**
- 헬스체크: 200 OK
- 모델: qwen3-vl 포함
- 응답 정상 생성

---

### TC-OCR-PREC-003: 프리미엄 OCR 이미지 분석

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PREC-003 |
| 테스트명 | VLM 기반 이미지 분석 및 텍스트 추출 |
| 우선순위 | High |
| 사전조건 | chandra-vllm 서비스 healthy |

**테스트 절차:**
1. 복잡한 레이아웃의 문서 이미지 준비
2. PRECISION 모드로 OCR 처리
3. 추출된 텍스트 및 구조 확인

**예상 결과:**
- 복잡한 레이아웃 정확히 인식
- 다단 구조 처리
- 헤더/푸터/본문 구분

---

### TC-OCR-PREC-004: 프리미엄 OCR 다국어 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PREC-004 |
| 테스트명 | VLM 다국어 문서 처리 |
| 우선순위 | Medium |
| 사전조건 | 한글/영어 혼합 문서 준비 |

**테스트 절차:**
1. 한글/영어 혼합 문서 업로드
2. PRECISION 모드로 OCR 처리
3. 언어별 텍스트 추출 확인

**예상 결과:**
- 한글/영어 모두 정확히 인식
- 언어 전환 부분 정확한 처리
- 특수문자 정상 인식

---

### TC-OCR-PREC-005: 프리미엄 OCR GPU 메모리 관리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PREC-005 |
| 테스트명 | VLM GPU 메모리 사용량 확인 |
| 우선순위 | High |
| 사전조건 | nvidia-smi 사용 가능 |

**테스트 절차:**
1. OCR 처리 전 GPU 메모리 확인
2. PRECISION OCR 처리 중 메모리 확인
3. 처리 완료 후 메모리 해제 확인

**예상 결과:**
- Qwen3-VL-30B-A3B 모델: 약 15-20GB VRAM 사용
- 처리 완료 후 메모리 안정화
- 메모리 누수 없음

**모니터링 스크립트:**
```bash
watch -n 1 nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv
```

---

### TC-OCR-PREC-006: 프리미엄 OCR 타임아웃 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PREC-006 |
| 테스트명 | VLM 요청 타임아웃 처리 |
| 우선순위 | Medium |
| 사전조건 | VLM_TIMEOUT 설정 확인 |

**테스트 절차:**
1. 매우 큰 이미지(고해상도) 업로드
2. PRECISION 모드로 OCR 처리
3. 타임아웃 발생 시 동작 확인

**예상 결과:**
- 120초 타임아웃 적용
- 타임아웃 시 적절한 에러 메시지
- 재시도 로직 동작

---

## 5. OCR 모드 자동 선택 테스트

### TC-OCR-AUTO-001: 자동 모드 선택 로직

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-AUTO-001 |
| 테스트명 | OCR 모드 자동 선택 (AUTO) |
| 우선순위 | High |
| 사전조건 | OCR_DEFAULT_MODE=auto 설정 |

**테스트 절차:**
1. 고품질 PDF 업로드 → FAST 모드 예상
2. 저품질 스캔 PDF 업로드 → ACCURATE 모드 예상
3. 복잡한 레이아웃 PDF 업로드 → PRECISION 모드 예상

**예상 결과:**
- 문서 품질에 따른 자동 모드 선택
- recommended_ocr_mode 필드 설정

---

### TC-OCR-AUTO-002: 신뢰도 임계값 기반 선택

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-AUTO-002 |
| 테스트명 | OCR_PRECISION_THRESHOLD 기반 모드 선택 |
| 우선순위 | Medium |
| 사전조건 | OCR_PRECISION_THRESHOLD=60 설정 |

**테스트 절차:**
1. 예비 분석으로 문서 품질 측정
2. 신뢰도 < 60% → PRECISION 모드 권장
3. 신뢰도 >= 60% → FAST/ACCURATE 모드 권장

**예상 결과:**
- 임계값 기반 정확한 모드 권장
- recommended_ocr_mode 필드 정확히 설정

---

## 6. OCR 에러 처리 테스트

### TC-OCR-ERR-001: 손상된 PDF 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ERR-001 |
| 테스트명 | 손상된 PDF 파일 OCR 처리 |
| 우선순위 | High |
| 사전조건 | 손상된 PDF 파일 준비 |

**테스트 절차:**
1. 손상된 PDF 파일 업로드
2. OCR 처리 요청
3. 에러 처리 확인

**예상 결과:**
- 상태: "failed"
- 적절한 에러 메시지
- 시스템 안정성 유지

---

### TC-OCR-ERR-002: 빈 문서 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ERR-002 |
| 테스트명 | 빈 페이지 문서 OCR 처리 |
| 우선순위 | Medium |
| 사전조건 | 빈 페이지만 있는 PDF 준비 |

**테스트 절차:**
1. 빈 페이지 PDF 업로드
2. OCR 처리 요청
3. 결과 확인

**예상 결과:**
- 상태: "completed"
- 빈 텍스트 결과
- 경고 메시지 (선택적)

---

### TC-OCR-ERR-003: Worker 장애 시 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ERR-003 |
| 테스트명 | OCR Worker 장애 시 작업 복구 |
| 우선순위 | High |
| 사전조건 | Redis 작업 큐 확인 가능 |

**테스트 절차:**
1. OCR 처리 요청
2. 처리 중 Worker 컨테이너 재시작
3. 작업 재처리 확인

**예상 결과:**
- 작업 큐에 재등록
- Worker 재시작 후 처리 완료
- 데이터 일관성 유지

**복구 테스트:**
```bash
# Worker 재시작
docker restart pbt_vlm_ocr-worker-fast-ocr-1

# 큐 확인
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN fast_ocr
```

---

### TC-OCR-ERR-004: VLM 서비스 장애 시 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-ERR-004 |
| 테스트명 | Chandra-VLLM 장애 시 PRECISION OCR 처리 |
| 우선순위 | Critical |
| 사전조건 | chandra-vllm 중지 가능 |

**테스트 절차:**
1. PRECISION OCR 처리 요청
2. chandra-vllm 컨테이너 중지
3. 에러 처리 확인

**예상 결과:**
- 적절한 에러 메시지
- 재시도 로직 동작
- 상태: "failed" 또는 "pending"

---

## 7. OCR 성능 테스트

### TC-OCR-PERF-001: 기본 OCR 처리 시간 측정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PERF-001 |
| 테스트명 | 기본 OCR 페이지당 처리 시간 |
| 우선순위 | High |
| 목표 | < 2초/페이지 |

**테스트 절차:**
1. 10페이지 PDF 업로드
2. FAST 모드로 OCR 처리
3. 총 처리 시간 측정

**성능 기준:**
- 평균: < 2초/페이지
- 최대: < 5초/페이지

---

### TC-OCR-PERF-002: 고급 OCR 처리 시간 측정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PERF-002 |
| 테스트명 | 고급 OCR 페이지당 처리 시간 |
| 우선순위 | High |
| 목표 | < 5초/페이지 |

**테스트 절차:**
1. 10페이지 PDF 업로드
2. ACCURATE 모드로 OCR 처리
3. 총 처리 시간 측정

**성능 기준:**
- 평균: < 5초/페이지
- 최대: < 15초/페이지

---

### TC-OCR-PERF-003: 프리미엄 OCR 처리 시간 측정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PERF-003 |
| 테스트명 | 프리미엄 OCR 페이지당 처리 시간 |
| 우선순위 | High |
| 목표 | < 10초/페이지 |

**테스트 절차:**
1. 10페이지 PDF 업로드
2. PRECISION 모드로 OCR 처리
3. GPU 사용률과 함께 시간 측정

**성능 기준:**
- 평균: < 10초/페이지
- 최대: < 30초/페이지
- GPU 사용률: > 50%

---

### TC-OCR-PERF-004: OCR 큐 처리량

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-PERF-004 |
| 테스트명 | OCR 큐 처리량 측정 |
| 우선순위 | Medium |
| 목표 | 10문서/분 (FAST 모드) |

**테스트 절차:**
1. 20개 문서 동시 업로드
2. FAST 모드로 모두 OCR 요청
3. 전체 처리 시간 측정

**성능 기준:**
- FAST: 10+ 문서/분
- ACCURATE: 4+ 문서/분
- PRECISION: 2+ 문서/분

---

## 8. Celery 작업 테스트

### TC-OCR-CEL-001: Celery 작업 상태 추적

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-CEL-001 |
| 테스트명 | Celery 작업 상태 추적 |
| 우선순위 | High |
| 사전조건 | Redis 연결 정상 |

**테스트 절차:**
1. OCR 작업 요청
2. task_id로 상태 조회
3. 상태 변경 추적 (PENDING → STARTED → SUCCESS)

**검증 명령:**
```bash
# Celery 작업 상태
docker exec pbt_vlm_ocr-backend-1 python -c "
from celery.result import AsyncResult
from app.core.celery_app import celery_app
result = AsyncResult('{task_id}', app=celery_app)
print(f'State: {result.state}')
print(f'Result: {result.result}')
"
```

---

### TC-OCR-CEL-002: Celery 큐 분리 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-CEL-002 |
| 테스트명 | OCR 모드별 Celery 큐 분리 |
| 우선순위 | High |
| 사전조건 | 3개 Worker 모두 실행 중 |

**테스트 절차:**
1. FAST 모드 요청 → fast_ocr 큐
2. ACCURATE 모드 요청 → accurate_ocr 큐
3. PRECISION 모드 요청 → precision_ocr 큐

**검증 명령:**
```bash
# 각 큐 확인
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN fast_ocr
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN accurate_ocr
docker exec pbt_vlm_ocr-redis-1 redis-cli LLEN precision_ocr
```

**예상 결과:**
- 각 모드가 올바른 큐로 라우팅
- Worker가 해당 큐만 처리

---

### TC-OCR-CEL-003: Celery Worker 동시성 설정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-OCR-CEL-003 |
| 테스트명 | Worker 동시성 설정 확인 |
| 우선순위 | Medium |
| 사전조건 | docker-compose.yml 확인 |

**예상 설정:**
- worker-fast-ocr: -c 4 (4개 동시 처리)
- worker-accurate-ocr: -c 2 (2개 동시 처리)
- worker-precision-ocr: -c 1 (1개 순차 처리, GPU 리소스 제한)

**검증 명령:**
```bash
docker exec pbt_vlm_ocr-worker-fast-ocr-1 celery -A app.core.celery_app inspect stats
```

---

## 9. 테스트 데이터

### 테스트용 샘플 파일

| 파일명 | 페이지 | 용도 |
|--------|--------|------|
| personnel_regulations.pdf | 3 | 한글 문서 기본 테스트 |
| labor_management_council_regulations.pdf | 3 | 한글 문서 고급 테스트 |
| sample_image.png | 1 | 이미지 OCR 테스트 |
| multi_column.pdf | 5 | 다단 레이아웃 테스트 |
| table_document.pdf | 2 | 테이블 인식 테스트 |
| low_quality_scan.pdf | 3 | 저품질 스캔 테스트 |
| mixed_language.pdf | 2 | 다국어 문서 테스트 |

---

## 10. 테스트 실행 스크립트

### 자동화 테스트 실행

```bash
#!/bin/bash
# OCR 모듈 테스트 실행 스크립트

echo "=== OCR 모듈 테스트 시작 ==="

# 1. 서비스 상태 확인
echo "[1/5] 서비스 상태 확인..."
docker compose ps

# 2. 기본 OCR 테스트
echo "[2/5] 기본 OCR 테스트..."
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=FAST"

# 3. 고급 OCR 테스트
echo "[3/5] 고급 OCR 테스트..."
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=ACCURATE"

# 4. 프리미엄 OCR 테스트 (GPU 확인)
echo "[4/5] 프리미엄 OCR 테스트..."
nvidia-smi &
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=PRECISION"

# 5. 결과 확인
echo "[5/5] 테스트 결과 확인..."
curl http://localhost:8000/api/v1/documents/ | jq '.items[-3:]'

echo "=== OCR 모듈 테스트 완료 ==="
```
