# PBT VLM OCR - 테스트 전략 및 개요

## 1. 문서 정보

| 항목 | 내용 |
|------|------|
| 프로젝트명 | PBT VLM OCR Solution |
| 버전 | 1.0.0 |
| 작성일 | 2026-01-01 |
| 작성자 | Development Team |

---

## 2. 테스트 범위

### 2.1 테스트 대상 모듈

| 모듈 | 설명 | 테스트 파일 |
|------|------|-------------|
| Backend API | FastAPI 기반 REST API | `01_API_TEST.md` |
| OCR 처리 | 3가지 OCR 모드 (기본/고급/프리미엄) | `02_OCR_MODULE_TEST.md` |
| Database | PostgreSQL 데이터 저장/조회 | `03_DATABASE_TEST.md` |
| Storage | MinIO 파일 저장/조회 | `04_STORAGE_TEST.md` |
| Frontend UI | Next.js 웹 인터페이스 | `05_FRONTEND_TEST.md` |
| 통합 테스트 | E2E 워크플로우 | `06_INTEGRATION_TEST.md` |
| 성능 테스트 | 부하/스트레스 테스트 | `07_PERFORMANCE_TEST.md` |
| 보안 테스트 | 취약점 검증 | `08_SECURITY_TEST.md` |

### 2.2 시스템 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                         Port: 3000                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                         Port: 8000                               │
├─────────────────────────────────────────────────────────────────┤
│  /api/v1/documents  │  /api/v1/files  │  /api/v1/settings       │
└─────────────────────────────────────────────────────────────────┘
         │                      │                    │
         ▼                      ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐
│  PostgreSQL │    │    MinIO    │    │         Redis           │
│  Port: 5432 │    │ Port: 9000  │    │      Port: 6379         │
└─────────────┘    └─────────────┘    └─────────────────────────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          ▼                    ▼                    ▼
                   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
                   │ Worker-Fast  │   │Worker-Accurate│   │Worker-Precision│
                   │  (Tesseract) │   │  (PaddleOCR)  │   │  (VLM GPU)   │
                   └──────────────┘   └──────────────┘   └──────────────┘
                                                                │
                                                                ▼
                                                       ┌──────────────┐
                                                       │ Chandra-VLLM │
                                                       │  Port: 8080  │
                                                       └──────────────┘
```

---

## 3. 테스트 환경

### 3.1 하드웨어 요구사항

| 구성요소 | 최소 사양 | 권장 사양 |
|----------|----------|----------|
| CPU | 8 cores | 16+ cores |
| RAM | 16GB | 32GB+ |
| GPU | - | NVIDIA RTX 3090 24GB |
| Storage | 50GB SSD | 200GB+ SSD |

### 3.2 소프트웨어 환경

| 구성요소 | 버전 |
|----------|------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| Python | 3.11 |
| Node.js | 20.x |
| PostgreSQL | 15 |
| Redis | 7 |

### 3.3 테스트 데이터

테스트용 샘플 파일 위치: `/data/`

| 파일명 | 형식 | 페이지 | 용도 |
|--------|------|--------|------|
| personnel_regulations.pdf | PDF | 3 | 한글 문서 테스트 |
| labor_management_council_regulations.pdf | PDF | 3 | 한글 문서 테스트 |
| sample_image.png | PNG | 1 | 이미지 OCR 테스트 |

---

## 4. 테스트 유형

### 4.1 단위 테스트 (Unit Test)
- 개별 함수/메서드 검증
- 모킹을 통한 의존성 분리
- 커버리지 목표: 80% 이상

### 4.2 통합 테스트 (Integration Test)
- 모듈 간 상호작용 검증
- 실제 DB/Storage 연동
- API 엔드포인트 테스트

### 4.3 E2E 테스트 (End-to-End Test)
- 전체 워크플로우 검증
- 사용자 시나리오 기반
- 브라우저 자동화 (Playwright)

### 4.4 성능 테스트 (Performance Test)
- 응답 시간 측정
- 동시 처리 능력
- 리소스 사용량 모니터링

### 4.5 보안 테스트 (Security Test)
- 인증/인가 검증
- 입력 검증
- CORS/CSRF 보호

---

## 5. 테스트 케이스 ID 체계

```
TC-{모듈}-{기능}-{번호}

예시:
- TC-API-DOC-001: API 문서 업로드 테스트 #1
- TC-OCR-FAST-003: 기본 OCR 테스트 #3
- TC-UI-LIST-002: UI 문서 목록 테스트 #2
```

### 모듈 코드

| 코드 | 모듈 |
|------|------|
| API | Backend REST API |
| OCR | OCR 처리 모듈 |
| DB | Database |
| STG | Storage (MinIO) |
| UI | Frontend UI |
| INT | Integration |
| PERF | Performance |
| SEC | Security |

---

## 6. 테스트 실행 방법

### 6.1 자동화 테스트 실행

```bash
# Backend 단위 테스트
cd backend
pytest tests/ -v --cov=app

# Frontend 테스트
cd frontend
npm test

# E2E 테스트
cd tests/e2e
npx playwright test
```

### 6.2 수동 테스트 실행

각 테스트 케이스 문서의 "테스트 절차"를 따라 수동으로 실행

### 6.3 성능 테스트 실행

```bash
# k6 부하 테스트
k6 run tests/performance/load_test.js

# 스트레스 테스트
k6 run tests/performance/stress_test.js
```

---

## 7. 결함 분류

### 7.1 심각도 (Severity)

| 등급 | 설명 | 예시 |
|------|------|------|
| Critical | 시스템 중단 | 서버 크래시, 데이터 손실 |
| High | 주요 기능 불가 | OCR 처리 실패, 파일 업로드 불가 |
| Medium | 기능 제한 | UI 깨짐, 일부 기능 오류 |
| Low | 사소한 문제 | 오타, 미미한 UI 이슈 |

### 7.2 우선순위 (Priority)

| 등급 | 조치 시한 |
|------|----------|
| P1 | 즉시 (24시간 이내) |
| P2 | 긴급 (72시간 이내) |
| P3 | 일반 (1주일 이내) |
| P4 | 낮음 (다음 릴리즈) |

---

## 8. 테스트 완료 기준

### 8.1 Exit Criteria

- [ ] 모든 Critical/High 결함 해결
- [ ] 테스트 케이스 실행률 100%
- [ ] 테스트 통과율 95% 이상
- [ ] 코드 커버리지 80% 이상
- [ ] 성능 목표 달성

### 8.2 성능 목표

| 지표 | 목표값 |
|------|--------|
| API 응답 시간 (평균) | < 200ms |
| 문서 업로드 시간 | < 3초 |
| 기본 OCR 처리 시간 (페이지당) | < 2초 |
| 고급 OCR 처리 시간 (페이지당) | < 5초 |
| 프리미엄 OCR 처리 시간 (페이지당) | < 10초 |
| 동시 사용자 | 50명 이상 |

---

## 9. 테스트 일정

| 단계 | 기간 | 담당 |
|------|------|------|
| 테스트 계획 수립 | 1일 | QA Lead |
| 테스트 케이스 작성 | 2일 | QA Team |
| 환경 구성 | 1일 | DevOps |
| 단위 테스트 | 2일 | Developer |
| 통합 테스트 | 2일 | QA Team |
| E2E 테스트 | 2일 | QA Team |
| 성능 테스트 | 1일 | QA Team |
| 결함 수정 | 3일 | Developer |
| 회귀 테스트 | 1일 | QA Team |

---

## 10. 관련 문서

- [API 테스트 케이스](./01_API_TEST.md)
- [OCR 모듈 테스트 케이스](./02_OCR_MODULE_TEST.md)
- [Database 테스트 케이스](./03_DATABASE_TEST.md)
- [Storage 테스트 케이스](./04_STORAGE_TEST.md)
- [Frontend 테스트 케이스](./05_FRONTEND_TEST.md)
- [통합 테스트 케이스](./06_INTEGRATION_TEST.md)
- [성능 테스트 케이스](./07_PERFORMANCE_TEST.md)
- [보안 테스트 케이스](./08_SECURITY_TEST.md)
