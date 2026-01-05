# PBT VLM OCR Suite

VLM(Vision Language Model) 기반의 고정밀 문서 OCR 시스템입니다.

## 주요 기능

- **다중 OCR 모드**: 속도와 정확도에 따른 3가지 OCR 모드 지원
  - **Fast OCR**: Tesseract 기반, CPU 전용, 빠른 처리
  - **Accurate OCR**: PaddleOCR 기반, CPU 전용, 높은 정확도
  - **Precision OCR**: Qwen3-VL 기반, GPU 필요, 최고 정확도
- **PDF 문서 처리**: PDF 업로드 및 페이지별 OCR 처리
- **실시간 처리 상태**: Celery 기반 비동기 작업 큐
- **문서 관리**: 검색, 필터링, 내보내기 기능
- **웹 기반 UI**: 직관적인 문서 뷰어 및 편집 기능

## 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11, Celery |
| Database | PostgreSQL 15, Redis 7 |
| Storage | MinIO (S3 호환) |
| Vector DB | Qdrant |
| VLM | Qwen3-VL-30B-A3B (vLLM) |

## 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  PostgreSQL │
│  (Next.js)  │     │  (FastAPI)  │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │     Redis (Queue)     │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  Fast Worker  │ │Accurate Worker│ │Precision Worker│
│  (Tesseract)  │ │  (PaddleOCR)  │ │   (Qwen3-VL)  │
└───────────────┘ └───────────────┘ └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │  VLM Server   │
                                    │    (vLLM)     │
                                    └───────────────┘
```

## 요구사항

- Docker & Docker Compose
- NVIDIA GPU (Precision OCR 사용 시)
- NVIDIA Container Toolkit (GPU 사용 시)

## 빠른 시작

### 1. 환경 설정

```bash
cp .env.example .env
```

### 2. 개발 환경 실행 (GPU 없음)

```bash
make dev
make init
```

### 3. 프로덕션 환경 실행 (GPU 포함)

```bash
make prod
make init
```

### 4. 접속

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

## 주요 명령어

```bash
# 개발 환경
make dev              # 개발 환경 시작
make down             # 모든 컨테이너 중지
make logs             # 로그 확인
make init             # DB/스토리지 초기화

# 데이터베이스
make migrate          # 마이그레이션 실행
make migrate-gen MSG="message"  # 새 마이그레이션 생성

# VLM (GPU OCR)
make vlm-start        # VLM 서버 시작
make vlm-stop         # VLM 서버 중지
make vlm-logs         # VLM 로그 확인
make vlm-test         # VLM 서버 테스트

# 기타
make clean            # 컨테이너 및 볼륨 삭제
make build            # 이미지 빌드
make test             # 테스트 실행
```

## 프로젝트 구조

```
PBT_VLM_OCR/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/v1/         # API 엔드포인트
│   │   ├── services/       # 비즈니스 로직
│   │   ├── schemas/        # Pydantic 스키마
│   │   └── db/             # 데이터베이스 설정
│   └── alembic/            # DB 마이그레이션
├── frontend/               # Next.js 프론트엔드
│   └── src/
│       ├── app/            # 페이지
│       ├── components/     # 컴포넌트
│       └── hooks/          # React 훅
├── workers/                # OCR 워커
│   ├── general_ocr/        # Tesseract 워커
│   ├── accurate_ocr/       # PaddleOCR 워커
│   └── precision_ocr/      # VLM 워커
├── scripts/                # 유틸리티 스크립트
├── docs/                   # 문서
├── docker-compose.yml      # 프로덕션 설정
└── docker-compose.dev.yml  # 개발 설정
```

## API 사용 예시

### 문서 업로드

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@document.pdf" \
  -F "ocr_mode=auto"
```

### 문서 목록 조회

```bash
curl http://localhost:8000/api/v1/documents
```

### 문서 상세 조회

```bash
curl http://localhost:8000/api/v1/documents/{document_id}
```

## 환경 변수

주요 환경 변수는 `.env.example` 파일을 참조하세요.

| 변수 | 설명 | 기본값 |
|------|------|--------|
| DATABASE_URL | PostgreSQL 연결 URL | postgresql://postgres:postgres@localhost:5432/pbt_ocr |
| REDIS_URL | Redis 연결 URL | redis://localhost:6379/0 |
| MINIO_ENDPOINT | MinIO 엔드포인트 | localhost:9000 |
| VLM_API_BASE | VLM 서버 URL | http://localhost:8080/v1 |

## 라이선스

MIT License
