PBT VLM OCR Suite – 최종 개발 문서 (PRD v1.2)

일반 OCR + VLM 기반 정밀 OCR 이중 엔진을 지원하는
사내 문서 OCR · 지식화 플랫폼

⸻

0. 문서 목적

본 문서는 PBT VLM OCR Suite의 최종 개발 기준 문서(PRD)로서,
	•	전체 시스템 아키텍처
	•	일반 OCR / 정밀 OCR(VLM) 이중 처리 전략
	•	OCR 모드 자동 추천 규칙
	•	프론트엔드·백엔드·AI 서빙·DB·인프라 설계
를 실제 구현 가능한 수준으로 통합 정의한다.

본 문서는 개발·보안·운영·확장까지 고려한 엔터프라이즈 기준 문서이다.

⸻

1. 제품 개요

1.1 제품 정의

PBT VLM OCR Suite는 기업 사내 문서를 업로드하면
일반 OCR 또는 VLM 기반 정밀 OCR을 선택/자동 추천하여 처리하고,
결과를 구조화·저장·검색·검수·수정·다운로드(MD/JSON/HTML) 할 수 있는
온프레미스 OCR & 문서 지식화 플랫폼이다.

1.2 핵심 가치
	•	문서 가치에 맞는 OCR 품질 선택
	•	구조 보존 기반 데이터 자산화
	•	GPU 효율 극대화
	•	완전 로컬/폐쇄망 운영

⸻

2. 기술 스택 개요

2.1 Frontend
	•	React + Next.js
	•	TypeScript
	•	PDF.js / Image Viewer
	•	SSR + CSR 혼합

2.2 Backend
	•	Python FastAPI
	•	Celery + Redis (비동기 Job)
	•	Pydantic 기반 스키마

2.3 AI / OCR
	•	일반 OCR: Tesseract / PaddleOCR
	•	정밀 OCR: VLM 기반(PBT OCR Engine)
	•	추론 서빙: vLLM / TorchServe

2.4 Database
	•	관계형 DB: PostgreSQL
	•	벡터 DB: Qdrant (임베딩/의미검색)
	•	Object Storage: MinIO

2.5 Infra
	•	Docker / Docker Compose
	•	GPU Server (RTX 3090 이상)
	•	폐쇄망 배포

⸻

3. 시스템 전체 아키텍처

[ Next.js UI ]
      |
[ FastAPI API Gateway ]
      |
[ OCR Orchestrator ]
      |
+-----------------------------+
|  OCR Worker Pool            |
|  - General OCR (CPU)        |
|  - Precision OCR (GPU/VLM)  |
+-----------------------------+
      |
[ Post-process & Normalizer ]
      |
+-----------+-----------+------------+
| PostgreSQL|   Qdrant  |   MinIO    |
+-----------+-----------+------------+


⸻

4. OCR 처리 전략 (이중 엔진)

4.1 OCR 모드 구분

구분	일반 OCR	정밀 OCR (VLM)
목적	대량/저비용	고정밀/구조화
GPU	❌	✅
표/다단	제한	우수
RAG 적합성	낮음	매우 높음


⸻

5. OCR 모드 자동 추천 규칙 (통합)

5.1 OCR 모드 선택 옵션
	•	general
	•	precision
	•	auto (기본값)

5.2 무조건 결정 규칙 (Override)

정밀 OCR 강제
	•	계약/재무/법무/연구 문서
	•	중요도 High
	•	스캔본 PDF + 표 감지

일반 OCR 강제
	•	텍스트 레이어 충분
	•	중요도 Low + 200p 이상

5.3 점수 기반 추천
	•	precision_score >= 60 → 정밀 OCR
	•	점수 요소:
	•	중요도(+30)
	•	문서 유형(+25)
	•	스캔본(+20)
	•	표/다단(+20)
	•	페이지 수(-15)

5.4 프리 OCR 기반 보정(선택)
	•	1~2페이지 일반 OCR 샘플
	•	품질 점수 < 0.75 → 정밀 OCR 상향

⸻

6. OCR 파이프라인 상세

6.1 공통
	1.	업로드
	2.	전처리(PDF 렌더, 이미지 보정)
	3.	OCR 엔진 선택
	4.	후처리/구조화
	5.	저장/검수

6.2 정밀 OCR 파이프라인
	•	고해상도 렌더(300~400DPI)
	•	VLM OCR 추론
	•	블록/표/읽기순서 추출
	•	구조화 JSON 생성

⸻

7. 데이터베이스 설계 요약

7.1 documents
	•	id, title, department, importance
	•	ocr_mode, recommended_ocr_mode
	•	status, created_at

7.2 document_pages
	•	document_id, page_no
	•	ocr_json(JSONB)
	•	layout_score, confidence

7.3 document_blocks
	•	type, bbox, text, table_json

7.4 embeddings (Qdrant)
	•	vector
	•	document_id, block_id

⸻

8. API 핵심 스펙
	•	POST /documents (업로드)
	•	GET /documents (조회/검색)
	•	PATCH /documents/{id}/blocks/{block_id} (수정)
	•	GET /documents/{id}/download?format=md|json|html

⸻

9. Frontend(UI) 구성

9.1 주요 화면
	•	문서 업로드 (OCR 모드 선택/추천 표시)
	•	문서 목록/검색
	•	OCR 결과 검수 화면
	•	블록/표 편집 UI
	•	다운로드 메뉴

⸻

10. VLM 서빙 환경 (PBT OCR Engine)

10.1 구조
	•	독립 컨테이너
	•	GPU 전용
	•	vLLM 기반

10.2 특징
	•	모델 버전 관리
	•	문서 유형별 모델 라우팅
	•	워커 수평 확장

⸻

11. Docker Compose 구성
	•	frontend (Next.js)
	•	backend (FastAPI)
	•	worker-general-ocr
	•	worker-precision-ocr (GPU)
	•	postgres
	•	redis
	•	minio
	•	qdrant

⸻

12. 보안/운영
	•	RBAC
	•	SSO/LDAP 연계
	•	Audit Log
	•	OCR 모드 사용 정책/쿼터

⸻

13. 단계별 개발 일정
	•	Phase 0: 설계/인프라 (2주)
	•	Phase 1: OCR MVP (5주)
	•	Phase 1.5: 검수/검색 (3주)
	•	Phase 2: 임베딩/RAG (4~6주)

⸻

14. Executive Summary

PBT VLM OCR Suite는
단순 OCR 도구가 아니라,
기업 문서를 AI가 이해 가능한 지식 자산으로 전환하는 인프라다.

⸻

(본 문서는 바로 개발 착수 가능한 최종 PRD 기준 문서이다.)