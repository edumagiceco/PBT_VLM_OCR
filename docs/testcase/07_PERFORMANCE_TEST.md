# 성능 테스트 케이스

## 1. 개요

시스템 성능, 부하, 스트레스 테스트 케이스입니다. 응답 시간, 처리량, 리소스 사용량을 검증합니다.

---

## 2. 성능 목표

| 지표 | 목표값 | 비고 |
|------|--------|------|
| API 응답 시간 (평균) | < 200ms | GET 요청 |
| 문서 업로드 시간 | < 3초 | 10MB 이하 |
| 기본 OCR 처리 시간 | < 2초/페이지 | Tesseract |
| 고급 OCR 처리 시간 | < 5초/페이지 | PaddleOCR |
| 프리미엄 OCR 처리 시간 | < 10초/페이지 | VLM GPU |
| 동시 사용자 | 50명 이상 | - |
| 시스템 가용성 | 99.9% | - |

---

## 3. API 응답 시간 테스트

### TC-PERF-API-001: 문서 목록 API 응답 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-API-001 |
| 테스트명 | 문서 목록 API 응답 시간 측정 |
| 우선순위 | High |
| 목표 | < 200ms |

**테스트 절차:**
```bash
# 단일 요청 응답 시간
for i in {1..10}; do
  curl -w "Time: %{time_total}s\n" -o /dev/null -s \
    http://localhost:8000/api/v1/documents/
done

# 통계 수집
curl -w "@curl-format.txt" -o /dev/null -s \
  http://localhost:8000/api/v1/documents/
```

**curl-format.txt:**
```
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
```

**예상 결과:**
- 평균 응답 시간 < 200ms
- 95 백분위 < 500ms

---

### TC-PERF-API-002: 문서 상세 API 응답 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-API-002 |
| 테스트명 | 문서 상세 (페이지/블록 포함) API 응답 시간 |
| 우선순위 | High |
| 목표 | < 500ms |

**테스트 절차:**
```bash
# 10페이지 문서 상세 조회
time curl -s http://localhost:8000/api/v1/documents/1 > /dev/null
```

**예상 결과:**
- 평균 < 500ms
- 조인 쿼리 최적화 확인

---

### TC-PERF-API-003: 파일 다운로드 속도

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-API-003 |
| 테스트명 | 원본 파일 다운로드 속도 |
| 우선순위 | Medium |
| 목표 | > 10MB/s |

**테스트 절차:**
```bash
# 10MB 파일 다운로드 시간
time curl -o /dev/null http://localhost:8000/api/v1/files/documents/1/download
```

**예상 결과:**
- 10MB 파일 < 1초
- 네트워크 대역폭 활용

---

## 4. OCR 처리 성능 테스트

### TC-PERF-OCR-001: 기본 OCR (Tesseract) 처리 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-OCR-001 |
| 테스트명 | Tesseract OCR 페이지당 처리 시간 |
| 우선순위 | Critical |
| 목표 | < 2초/페이지 |

**테스트 절차:**
```bash
# 10페이지 문서 처리 시간 측정
START=$(date +%s.%N)

curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/10page.pdf" \
  -F "ocr_mode=FAST"

# 완료 대기
DOC_ID=...
while [ "$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.status')" != "completed" ]; do
  sleep 1
done

END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)
echo "Total: ${ELAPSED}s, Per page: $(echo "$ELAPSED / 10" | bc -l)s"
```

**예상 결과:**
- 페이지당 평균 < 2초
- CPU 사용률 모니터링

---

### TC-PERF-OCR-002: 고급 OCR (PaddleOCR) 처리 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-OCR-002 |
| 테스트명 | PaddleOCR 페이지당 처리 시간 |
| 우선순위 | Critical |
| 목표 | < 5초/페이지 |

**테스트 절차:**
```bash
time curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/3page.pdf" \
  -F "ocr_mode=ACCURATE"
```

**예상 결과:**
- 페이지당 평균 < 5초
- PP-OCRv5 모델 사용 확인

---

### TC-PERF-OCR-003: 프리미엄 OCR (VLM) 처리 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-OCR-003 |
| 테스트명 | VLM GPU OCR 페이지당 처리 시간 |
| 우선순위 | Critical |
| 목표 | < 10초/페이지 |

**테스트 절차:**
```bash
# GPU 모니터링 시작
nvidia-smi dmon -s u -d 1 > /tmp/gpu_perf.log &
GPU_PID=$!

# OCR 처리
curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/3page.pdf" \
  -F "ocr_mode=PRECISION"

# 완료 대기 후 GPU 모니터링 종료
kill $GPU_PID

# 결과 분석
cat /tmp/gpu_perf.log
```

**예상 결과:**
- 페이지당 평균 < 10초
- GPU 사용률 > 50%
- VRAM 사용량 모니터링

---

### TC-PERF-OCR-004: OCR 큐 처리량

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-OCR-004 |
| 테스트명 | OCR 큐 시간당 처리량 측정 |
| 우선순위 | High |
| 목표 | FAST 10문서/분, ACCURATE 4문서/분 |

**테스트 절차:**
```bash
# 20개 문서 업로드 후 전체 완료 시간 측정
START=$(date +%s)

for i in {1..20}; do
  curl -s -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/sample.pdf" \
    -F "ocr_mode=FAST" &
done
wait

# 모든 문서 완료 대기
while true; do
  PENDING=$(curl -s http://localhost:8000/api/v1/documents/ | jq '[.items[] | select(.status != "completed")] | length')
  if [ "$PENDING" -eq 0 ]; then break; fi
  sleep 5
done

END=$(date +%s)
echo "Total time: $((END - START)) seconds"
echo "Throughput: $(echo "20 / ($END - $START) * 60" | bc -l) docs/min"
```

---

## 5. 부하 테스트

### TC-PERF-LOAD-001: 동시 사용자 부하 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-LOAD-001 |
| 테스트명 | 50명 동시 사용자 시뮬레이션 |
| 우선순위 | Critical |
| 목표 | 에러율 < 1% |

**k6 테스트 스크립트:**
```javascript
// tests/performance/load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 10 },  // 램프업
    { duration: '3m', target: 50 },  // 유지
    { duration: '1m', target: 0 },   // 램프다운
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  // 문서 목록 조회
  let listRes = http.get('http://localhost:8000/api/v1/documents/');
  check(listRes, {
    'list status 200': (r) => r.status === 200,
    'list duration < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);

  // 문서 상세 조회
  let detailRes = http.get('http://localhost:8000/api/v1/documents/1');
  check(detailRes, {
    'detail status 200': (r) => r.status === 200,
  });

  sleep(1);
}
```

**실행:**
```bash
k6 run tests/performance/load_test.js
```

**예상 결과:**
- 에러율 < 1%
- 95 백분위 응답 시간 < 500ms

---

### TC-PERF-LOAD-002: 파일 업로드 부하 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-LOAD-002 |
| 테스트명 | 동시 파일 업로드 부하 테스트 |
| 우선순위 | High |
| 목표 | 10개 동시 업로드 성공 |

**k6 테스트 스크립트:**
```javascript
import http from 'k6/http';
import { check } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';

export let options = {
  vus: 10,
  duration: '1m',
};

const file = open('/data/sample.pdf', 'b');

export default function () {
  const fd = new FormData();
  fd.append('file', http.file(file, 'sample.pdf'));
  fd.append('ocr_mode', 'FAST');

  let res = http.post('http://localhost:8000/api/v1/documents/', fd.body(), {
    headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd.boundary },
  });

  check(res, {
    'upload success': (r) => r.status === 200 || r.status === 201,
  });
}
```

---

### TC-PERF-LOAD-003: 혼합 워크로드 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-LOAD-003 |
| 테스트명 | 읽기/쓰기 혼합 부하 |
| 우선순위 | High |
| 목표 | 읽기 80%, 쓰기 20% |

**테스트 스크립트:**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 30,
  duration: '5m',
};

export default function () {
  if (Math.random() < 0.8) {
    // 80% 읽기
    http.get('http://localhost:8000/api/v1/documents/');
  } else {
    // 20% 쓰기 (업로드)
    // ... 업로드 로직
  }
  sleep(0.5);
}
```

---

## 6. 스트레스 테스트

### TC-PERF-STRESS-001: 최대 처리 용량 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-STRESS-001 |
| 테스트명 | 시스템 한계 처리량 측정 |
| 우선순위 | High |
| 목표 | 중단점 확인 |

**k6 스트레스 테스트:**
```javascript
export let options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '2m', target: 150 },
    { duration: '2m', target: 200 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  http.get('http://localhost:8000/api/v1/documents/');
}
```

**예상 결과:**
- 중단점(breaking point) 식별
- 에러 발생 시점 기록
- 복구 시간 측정

---

### TC-PERF-STRESS-002: 메모리 스트레스 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-STRESS-002 |
| 테스트명 | 대용량 문서 연속 처리 시 메모리 |
| 우선순위 | High |
| 목표 | 메모리 누수 없음 |

**테스트 절차:**
```bash
# 메모리 모니터링 시작
docker stats --format "table {{.Name}}\t{{.MemUsage}}" > /tmp/mem_log.txt &
STATS_PID=$!

# 대용량 문서 연속 업로드
for i in {1..50}; do
  curl -s -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/10page.pdf" \
    -F "ocr_mode=FAST"
  sleep 2
done

# 모니터링 종료
kill $STATS_PID

# 메모리 사용량 분석
cat /tmp/mem_log.txt
```

**예상 결과:**
- 메모리 사용량 안정적
- GC 정상 동작
- OOM 없음

---

### TC-PERF-STRESS-003: GPU 메모리 스트레스 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-STRESS-003 |
| 테스트명 | VLM 연속 처리 시 GPU 메모리 |
| 우선순위 | High |
| 목표 | VRAM 누수 없음 |

**테스트 절차:**
```bash
# GPU 메모리 모니터링
nvidia-smi --query-gpu=timestamp,memory.used,memory.total --format=csv -l 5 > /tmp/gpu_mem.csv &
GPU_PID=$!

# PRECISION OCR 연속 처리
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/3page.pdf" \
    -F "ocr_mode=PRECISION"
  sleep 60  # 처리 완료 대기
done

kill $GPU_PID

# 분석
cat /tmp/gpu_mem.csv
```

**예상 결과:**
- VRAM 사용량 안정적 (약 15-20GB)
- 누수 없음
- 처리 후 메모리 해제

---

## 7. 리소스 사용량 테스트

### TC-PERF-RES-001: CPU 사용량 모니터링

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-RES-001 |
| 테스트명 | 서비스별 CPU 사용량 |
| 우선순위 | Medium |
| 목표 | 각 서비스 < 80% |

**테스트 절차:**
```bash
# 컨테이너별 CPU 사용량
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"
```

---

### TC-PERF-RES-002: 메모리 사용량 모니터링

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-RES-002 |
| 테스트명 | 서비스별 메모리 사용량 |
| 우선순위 | Medium |
| 목표 | 각 서비스 < 할당량 80% |

**테스트 절차:**
```bash
# 컨테이너별 메모리 사용량
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

---

### TC-PERF-RES-003: 디스크 I/O 모니터링

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-RES-003 |
| 테스트명 | 디스크 I/O 성능 |
| 우선순위 | Low |
| 목표 | I/O 병목 없음 |

**테스트 절차:**
```bash
# 디스크 I/O 모니터링
iostat -x 1 10
```

---

### TC-PERF-RES-004: 네트워크 대역폭 모니터링

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-RES-004 |
| 테스트명 | 네트워크 사용량 |
| 우선순위 | Low |
| 목표 | 네트워크 병목 없음 |

**테스트 절차:**
```bash
# 네트워크 사용량
docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"
```

---

## 8. 데이터베이스 성능 테스트

### TC-PERF-DB-001: 쿼리 실행 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-DB-001 |
| 테스트명 | 주요 쿼리 실행 시간 측정 |
| 우선순위 | High |
| 목표 | 평균 < 50ms |

**테스트 절차:**
```sql
-- 쿼리 실행 시간 분석
EXPLAIN ANALYZE
SELECT d.*,
  (SELECT COUNT(*) FROM pages WHERE document_id = d.id) as page_count,
  (SELECT COUNT(*) FROM blocks WHERE page_id IN (SELECT id FROM pages WHERE document_id = d.id)) as block_count
FROM documents d
ORDER BY d.created_at DESC
LIMIT 20;
```

---

### TC-PERF-DB-002: 연결 풀 성능

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-DB-002 |
| 테스트명 | DB 연결 풀 효율성 |
| 우선순위 | Medium |
| 목표 | 연결 대기 없음 |

**테스트 절차:**
```sql
-- 활성 연결 수 확인
SELECT count(*), state FROM pg_stat_activity
WHERE datname = 'pbt_ocr'
GROUP BY state;
```

---

## 9. 캐시 성능 테스트

### TC-PERF-CACHE-001: Redis 응답 시간

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-CACHE-001 |
| 테스트명 | Redis 캐시 응답 시간 |
| 우선순위 | Medium |
| 목표 | < 10ms |

**테스트 절차:**
```bash
# Redis 벤치마크
docker exec pbt_vlm_ocr-redis-1 redis-benchmark -t get,set -n 10000
```

---

## 10. 장기 실행 테스트

### TC-PERF-LONG-001: 24시간 안정성 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-PERF-LONG-001 |
| 테스트명 | 24시간 연속 운영 안정성 |
| 우선순위 | High |
| 목표 | 성능 저하 없음 |

**테스트 절차:**
```bash
#!/bin/bash
# 24시간 모니터링 스크립트

DURATION=86400  # 24시간
INTERVAL=300    # 5분마다 기록

START=$(date +%s)
while [ $(($(date +%s) - START)) -lt $DURATION ]; do
  echo "=== $(date) ===" >> /tmp/long_test.log

  # API 응답 시간
  curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/api/v1/documents/ >> /tmp/long_test.log

  # 리소스 사용량
  docker stats --no-stream >> /tmp/long_test.log

  sleep $INTERVAL
done
```

---

## 11. 벤치마크 결과 템플릿

### 성능 테스트 결과 기록

| 테스트 항목 | 측정값 | 목표값 | 결과 |
|-------------|--------|--------|------|
| API 목록 응답 시간 (평균) | ms | < 200ms | |
| API 목록 응답 시간 (p95) | ms | < 500ms | |
| 문서 상세 응답 시간 | ms | < 500ms | |
| 기본 OCR (페이지당) | s | < 2s | |
| 고급 OCR (페이지당) | s | < 5s | |
| 프리미엄 OCR (페이지당) | s | < 10s | |
| 동시 사용자 50명 에러율 | % | < 1% | |
| 메모리 사용량 (Backend) | MB | < 1GB | |
| GPU 메모리 사용량 | GB | < 20GB | |

---

## 12. 자동화 성능 테스트 스크립트

```bash
#!/bin/bash
# 성능 테스트 실행 스크립트

echo "=== PBT VLM OCR 성능 테스트 시작 ==="

# 1. API 응답 시간 테스트
echo "[1/5] API 응답 시간 테스트..."
for i in {1..10}; do
  TIME=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8000/api/v1/documents/)
  echo "Request $i: ${TIME}s"
done

# 2. OCR 처리 시간 테스트
echo "[2/5] OCR 처리 시간 테스트..."
START=$(date +%s.%N)
DOC_ID=$(curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/data/personnel_regulations.pdf" \
  -F "ocr_mode=FAST" | jq -r '.id')

while [ "$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | jq -r '.status')" != "completed" ]; do
  sleep 1
done
END=$(date +%s.%N)
echo "FAST OCR (3 pages): $(echo "$END - $START" | bc)s"

# 3. 리소스 사용량
echo "[3/5] 리소스 사용량..."
docker stats --no-stream

# 4. 부하 테스트 (간단)
echo "[4/5] 간단한 부하 테스트..."
for i in {1..10}; do
  curl -s http://localhost:8000/api/v1/documents/ > /dev/null &
done
wait

# 5. GPU 상태 (있는 경우)
echo "[5/5] GPU 상태..."
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv 2>/dev/null || echo "GPU 없음"

echo "=== 성능 테스트 완료 ==="
```

---

## 13. k6 부하 테스트 설정

```javascript
// tests/performance/full_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const listDuration = new Trend('list_duration');
const detailDuration = new Trend('detail_duration');

export let options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 30 },
    { duration: '2m', target: 50 },
    { duration: '1m', target: 30 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    errors: ['rate<0.01'],
    list_duration: ['p(95)<500'],
    detail_duration: ['p(95)<1000'],
  },
};

const BASE_URL = 'http://localhost:8000/api/v1';

export default function () {
  // 문서 목록
  let listRes = http.get(`${BASE_URL}/documents/`);
  listDuration.add(listRes.timings.duration);
  let listCheck = check(listRes, {
    'list status 200': (r) => r.status === 200,
  });
  errorRate.add(!listCheck);

  sleep(0.5);

  // 문서 상세 (ID 1 가정)
  let detailRes = http.get(`${BASE_URL}/documents/1`);
  detailDuration.add(detailRes.timings.duration);
  let detailCheck = check(detailRes, {
    'detail status 200': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(!detailCheck && detailRes.status !== 404);

  sleep(0.5);
}
```

**실행:**
```bash
k6 run tests/performance/full_load_test.js --out json=results.json
```
