# Database 테스트 케이스

## 1. 개요

PostgreSQL 데이터베이스에 대한 테스트 케이스입니다. 데이터 저장, 조회, 무결성, 성능을 검증합니다.

---

## 2. 연결 테스트

### TC-DB-CONN-001: PostgreSQL 연결 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CONN-001 |
| 테스트명 | PostgreSQL 서버 연결 확인 |
| 우선순위 | Critical |
| 사전조건 | postgres 컨테이너 실행 중 |

**테스트 절차:**
```bash
# 컨테이너에서 직접 연결
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "SELECT 1;"

# Backend에서 연결 확인
docker exec pbt_vlm_ocr-backend-1 python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print(result.fetchone()[0])
"
```

**예상 결과:**
- 연결 성공
- PostgreSQL 버전 정보 반환

---

### TC-DB-CONN-002: 연결 풀 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CONN-002 |
| 테스트명 | SQLAlchemy 연결 풀 설정 확인 |
| 우선순위 | Medium |
| 사전조건 | Backend 서비스 실행 중 |

**테스트 절차:**
```bash
# 활성 연결 수 확인
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'pbt_ocr';
"
```

**예상 결과:**
- 연결 풀 정상 동작
- 유휴 연결 관리

---

## 3. 스키마 테스트

### TC-DB-SCH-001: 테이블 존재 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-SCH-001 |
| 테스트명 | 필수 테이블 존재 확인 |
| 우선순위 | Critical |
| 사전조건 | 데이터베이스 초기화 완료 |

**테스트 절차:**
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**예상 결과 (필수 테이블):**
- documents
- pages
- blocks
- alembic_version

---

### TC-DB-SCH-002: documents 테이블 스키마

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-SCH-002 |
| 테스트명 | documents 테이블 컬럼 확인 |
| 우선순위 | High |
| 사전조건 | documents 테이블 존재 |

**테스트 절차:**
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'documents'
ORDER BY ordinal_position;
```

**예상 컬럼:**
| 컬럼명 | 타입 | Nullable | 설명 |
|--------|------|----------|------|
| id | integer | NO | PK, 자동증가 |
| original_filename | varchar | NO | 원본 파일명 |
| storage_path | varchar | NO | MinIO 경로 |
| file_size | bigint | YES | 파일 크기 |
| mime_type | varchar | YES | MIME 타입 |
| page_count | integer | YES | 페이지 수 |
| status | varchar | NO | 처리 상태 |
| ocr_mode | ocrmode | YES | OCR 모드 |
| recommended_ocr_mode | ocrmode | YES | 권장 OCR 모드 |
| confidence | double precision | YES | 신뢰도 |
| processing_time | double precision | YES | 처리 시간 |
| created_at | timestamp | NO | 생성일시 |
| updated_at | timestamp | YES | 수정일시 |

---

### TC-DB-SCH-003: pages 테이블 스키마

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-SCH-003 |
| 테스트명 | pages 테이블 컬럼 및 FK 확인 |
| 우선순위 | High |
| 사전조건 | pages 테이블 존재 |

**테스트 절차:**
```sql
-- 컬럼 확인
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'pages';

-- FK 확인
SELECT tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'pages';
```

**예상 결과:**
- document_id → documents(id) FK 존재
- ON DELETE CASCADE 설정

---

### TC-DB-SCH-004: blocks 테이블 스키마

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-SCH-004 |
| 테스트명 | blocks 테이블 컬럼 및 FK 확인 |
| 우선순위 | High |
| 사전조건 | blocks 테이블 존재 |

**테스트 절차:**
```sql
-- 컬럼 확인
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'blocks';

-- FK 확인
SELECT tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'blocks';
```

**예상 결과:**
- page_id → pages(id) FK 존재
- ON DELETE CASCADE 설정

---

### TC-DB-SCH-005: ocrmode Enum 타입 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-SCH-005 |
| 테스트명 | ocrmode Enum 값 확인 |
| 우선순위 | High |
| 사전조건 | ocrmode 타입 존재 |

**테스트 절차:**
```sql
SELECT enumlabel FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'ocrmode');
```

**예상 결과:**
- FAST
- ACCURATE
- PRECISION
- (하위 호환: fast, accurate, precision)

---

## 4. CRUD 테스트

### TC-DB-CRUD-001: Document 생성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CRUD-001 |
| 테스트명 | Document 레코드 생성 |
| 우선순위 | Critical |
| 사전조건 | documents 테이블 존재 |

**테스트 절차:**
```sql
INSERT INTO documents (original_filename, storage_path, file_size, mime_type, status, created_at)
VALUES ('test.pdf', 'test/test.pdf', 1024, 'application/pdf', 'pending', NOW())
RETURNING id;
```

**예상 결과:**
- id 자동 생성
- created_at 자동 설정
- 레코드 정상 삽입

---

### TC-DB-CRUD-002: Document 조회

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CRUD-002 |
| 테스트명 | Document 레코드 조회 |
| 우선순위 | Critical |
| 사전조건 | 테스트 데이터 존재 |

**테스트 절차:**
```sql
-- 단일 조회
SELECT * FROM documents WHERE id = 1;

-- 목록 조회 (페이지네이션)
SELECT * FROM documents ORDER BY created_at DESC LIMIT 10 OFFSET 0;

-- 상태별 조회
SELECT * FROM documents WHERE status = 'completed';
```

**예상 결과:**
- 정확한 레코드 반환
- 정렬 및 페이지네이션 정상 동작

---

### TC-DB-CRUD-003: Document 수정

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CRUD-003 |
| 테스트명 | Document 레코드 수정 |
| 우선순위 | High |
| 사전조건 | 수정할 레코드 존재 |

**테스트 절차:**
```sql
UPDATE documents
SET status = 'completed',
    confidence = 0.95,
    processing_time = 5.5,
    updated_at = NOW()
WHERE id = 1;

SELECT status, confidence, processing_time, updated_at FROM documents WHERE id = 1;
```

**예상 결과:**
- 값 정상 업데이트
- updated_at 갱신

---

### TC-DB-CRUD-004: Document 삭제 (Cascade)

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CRUD-004 |
| 테스트명 | Document 삭제 시 연관 데이터 Cascade 삭제 |
| 우선순위 | Critical |
| 사전조건 | 연관 pages, blocks 데이터 존재 |

**테스트 절차:**
```sql
-- 삭제 전 카운트
SELECT
  (SELECT COUNT(*) FROM pages WHERE document_id = 1) as pages_before,
  (SELECT COUNT(*) FROM blocks WHERE page_id IN (SELECT id FROM pages WHERE document_id = 1)) as blocks_before;

-- Document 삭제
DELETE FROM documents WHERE id = 1;

-- 삭제 후 카운트
SELECT
  (SELECT COUNT(*) FROM pages WHERE document_id = 1) as pages_after,
  (SELECT COUNT(*) FROM blocks WHERE page_id IN (SELECT id FROM pages WHERE document_id = 1)) as blocks_after;
```

**예상 결과:**
- pages, blocks 자동 삭제
- 고아 레코드 없음

---

### TC-DB-CRUD-005: Page 생성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CRUD-005 |
| 테스트명 | Page 레코드 생성 |
| 우선순위 | High |
| 사전조건 | 상위 document 존재 |

**테스트 절차:**
```sql
INSERT INTO pages (document_id, page_no, image_path, width, height, confidence)
VALUES (1, 1, 'pages/1/1.png', 1200, 1600, 0.92)
RETURNING id;
```

**예상 결과:**
- page_no 1부터 시작
- document_id FK 검증

---

### TC-DB-CRUD-006: Block 생성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-CRUD-006 |
| 테스트명 | Block 레코드 생성 |
| 우선순위 | High |
| 사전조건 | 상위 page 존재 |

**테스트 절차:**
```sql
INSERT INTO blocks (page_id, block_order, block_type, text, bbox, confidence)
VALUES (1, 0, 'text', '테스트 텍스트입니다.', ARRAY[0.1, 0.1, 0.9, 0.2], 0.95)
RETURNING id;
```

**예상 결과:**
- bbox ARRAY 타입 정상 저장
- block_type Enum 검증

---

## 5. 무결성 테스트

### TC-DB-INT-001: FK 제약 조건 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-INT-001 |
| 테스트명 | 외래키 제약 조건 위반 테스트 |
| 우선순위 | Critical |
| 사전조건 | FK 제약 조건 설정됨 |

**테스트 절차:**
```sql
-- 존재하지 않는 document_id로 page 생성 시도
INSERT INTO pages (document_id, page_no, image_path)
VALUES (99999, 1, 'test.png');
```

**예상 결과:**
- 에러: `violates foreign key constraint`
- 삽입 실패

---

### TC-DB-INT-002: NOT NULL 제약 조건 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-INT-002 |
| 테스트명 | NOT NULL 필드 검증 |
| 우선순위 | High |
| 사전조건 | NOT NULL 제약 조건 설정됨 |

**테스트 절차:**
```sql
-- original_filename NULL로 document 생성 시도
INSERT INTO documents (original_filename, storage_path, status, created_at)
VALUES (NULL, 'test/test.pdf', 'pending', NOW());
```

**예상 결과:**
- 에러: `violates not-null constraint`
- 삽입 실패

---

### TC-DB-INT-003: Enum 제약 조건 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-INT-003 |
| 테스트명 | OCR Mode Enum 값 검증 |
| 우선순위 | High |
| 사전조건 | ocrmode Enum 타입 존재 |

**테스트 절차:**
```sql
-- 잘못된 Enum 값으로 업데이트 시도
UPDATE documents SET ocr_mode = 'INVALID_MODE' WHERE id = 1;
```

**예상 결과:**
- 에러: `invalid input value for enum ocrmode`
- 업데이트 실패

---

### TC-DB-INT-004: 중복 데이터 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-INT-004 |
| 테스트명 | 동일 문서 중복 페이지 번호 검증 |
| 우선순위 | Medium |
| 사전조건 | UNIQUE 제약 조건 존재 시 |

**테스트 절차:**
```sql
-- 동일 document_id, page_no로 2개 page 생성 시도
INSERT INTO pages (document_id, page_no, image_path) VALUES (1, 1, 'page1.png');
INSERT INTO pages (document_id, page_no, image_path) VALUES (1, 1, 'page1_dup.png');
```

**예상 결과:**
- UNIQUE 제약 조건 있으면: 에러
- 없으면: 정상 삽입 (데이터 설계 확인 필요)

---

## 6. 쿼리 성능 테스트

### TC-DB-PERF-001: 문서 목록 조회 성능

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-PERF-001 |
| 테스트명 | 문서 목록 페이지네이션 쿼리 성능 |
| 우선순위 | High |
| 목표 | < 50ms |

**테스트 절차:**
```sql
EXPLAIN ANALYZE
SELECT * FROM documents
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

**예상 결과:**
- Execution Time < 50ms
- Index Scan 사용 (created_at 인덱스 필요)

---

### TC-DB-PERF-002: 문서 상세 조회 성능

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-PERF-002 |
| 테스트명 | 문서+페이지+블록 조인 쿼리 성능 |
| 우선순위 | High |
| 목표 | < 100ms |

**테스트 절차:**
```sql
EXPLAIN ANALYZE
SELECT d.*, p.*, b.*
FROM documents d
LEFT JOIN pages p ON d.id = p.document_id
LEFT JOIN blocks b ON p.id = b.page_id
WHERE d.id = 1
ORDER BY p.page_no, b.block_order;
```

**예상 결과:**
- Execution Time < 100ms
- Nested Loop 또는 Hash Join 사용

---

### TC-DB-PERF-003: 상태별 문서 필터링 성능

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-PERF-003 |
| 테스트명 | 상태별 문서 필터링 쿼리 성능 |
| 우선순위 | Medium |
| 목표 | < 30ms |

**테스트 절차:**
```sql
EXPLAIN ANALYZE
SELECT * FROM documents
WHERE status = 'processing'
ORDER BY created_at DESC;
```

**예상 결과:**
- Execution Time < 30ms
- status 컬럼 인덱스 권장

---

### TC-DB-PERF-004: 대량 데이터 삽입 성능

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-PERF-004 |
| 테스트명 | 블록 대량 삽입 성능 |
| 우선순위 | Medium |
| 목표 | < 1초/100블록 |

**테스트 절차:**
```python
# 100개 블록 배치 삽입
import time
start = time.time()

# SQLAlchemy bulk_insert_mappings 사용
blocks = [
    {"page_id": 1, "block_order": i, "block_type": "text", "text": f"Block {i}"}
    for i in range(100)
]
session.bulk_insert_mappings(Block, blocks)
session.commit()

print(f"Elapsed: {time.time() - start:.3f}s")
```

**예상 결과:**
- 100개 블록 삽입 < 1초
- 트랜잭션 정상 완료

---

## 7. 인덱스 테스트

### TC-DB-IDX-001: 인덱스 존재 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-IDX-001 |
| 테스트명 | 필수 인덱스 존재 확인 |
| 우선순위 | High |
| 사전조건 | 데이터베이스 초기화 완료 |

**테스트 절차:**
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

**권장 인덱스:**
- documents(created_at)
- documents(status)
- pages(document_id)
- blocks(page_id)

---

### TC-DB-IDX-002: 인덱스 사용 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-IDX-002 |
| 테스트명 | 쿼리에서 인덱스 사용 확인 |
| 우선순위 | Medium |
| 사전조건 | 인덱스 생성됨 |

**테스트 절차:**
```sql
-- 실행 계획 확인
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM documents WHERE status = 'completed' ORDER BY created_at DESC LIMIT 10;
```

**예상 결과:**
- "Index Scan" 또는 "Index Only Scan" 사용
- Seq Scan 미사용

---

## 8. 트랜잭션 테스트

### TC-DB-TXN-001: 트랜잭션 원자성

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-TXN-001 |
| 테스트명 | 트랜잭션 롤백 테스트 |
| 우선순위 | Critical |
| 사전조건 | PostgreSQL 연결 정상 |

**테스트 절차:**
```sql
BEGIN;
INSERT INTO documents (original_filename, storage_path, status, created_at)
VALUES ('txn_test.pdf', 'test/txn.pdf', 'pending', NOW());
-- 의도적 에러 발생
SELECT 1/0;
ROLLBACK;

-- 데이터 확인
SELECT * FROM documents WHERE original_filename = 'txn_test.pdf';
```

**예상 결과:**
- 롤백으로 인해 데이터 없음
- 트랜잭션 원자성 보장

---

### TC-DB-TXN-002: 동시성 제어

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-TXN-002 |
| 테스트명 | 동시 업데이트 충돌 처리 |
| 우선순위 | High |
| 사전조건 | 테스트 레코드 존재 |

**테스트 절차:**
```python
# 두 세션에서 동시에 같은 레코드 업데이트
# Session 1
session1.query(Document).filter_by(id=1).update({"status": "processing"})

# Session 2 (동시)
session2.query(Document).filter_by(id=1).update({"status": "completed"})

# 양쪽 커밋
session1.commit()
session2.commit()
```

**예상 결과:**
- 마지막 커밋 값 적용
- 데드락 없음

---

## 9. 마이그레이션 테스트

### TC-DB-MIG-001: Alembic 마이그레이션 상태

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-MIG-001 |
| 테스트명 | Alembic 마이그레이션 버전 확인 |
| 우선순위 | High |
| 사전조건 | alembic_version 테이블 존재 |

**테스트 절차:**
```bash
# 현재 버전 확인
docker exec pbt_vlm_ocr-backend-1 alembic current

# 히스토리 확인
docker exec pbt_vlm_ocr-backend-1 alembic history
```

**예상 결과:**
- 최신 마이그레이션 버전
- head와 일치

---

### TC-DB-MIG-002: 마이그레이션 업그레이드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-MIG-002 |
| 테스트명 | 마이그레이션 업그레이드 실행 |
| 우선순위 | High |
| 사전조건 | 대기 중인 마이그레이션 존재 |

**테스트 절차:**
```bash
docker exec pbt_vlm_ocr-backend-1 alembic upgrade head
```

**예상 결과:**
- 에러 없이 완료
- 스키마 변경 적용

---

### TC-DB-MIG-003: 마이그레이션 다운그레이드

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-MIG-003 |
| 테스트명 | 마이그레이션 롤백 테스트 |
| 우선순위 | Medium |
| 사전조건 | 다운그레이드 가능한 마이그레이션 존재 |

**테스트 절차:**
```bash
# 1단계 롤백
docker exec pbt_vlm_ocr-backend-1 alembic downgrade -1

# 다시 업그레이드
docker exec pbt_vlm_ocr-backend-1 alembic upgrade head
```

**예상 결과:**
- 롤백 정상 실행
- 재업그레이드 성공

---

## 10. 백업/복구 테스트

### TC-DB-BAK-001: 데이터베이스 백업

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-BAK-001 |
| 테스트명 | PostgreSQL 백업 생성 |
| 우선순위 | High |
| 사전조건 | 데이터 존재 |

**테스트 절차:**
```bash
# SQL 백업
docker exec pbt_vlm_ocr-postgres-1 pg_dump -U postgres pbt_ocr > backup.sql

# 바이너리 백업
docker exec pbt_vlm_ocr-postgres-1 pg_dump -U postgres -Fc pbt_ocr > backup.dump
```

**예상 결과:**
- 백업 파일 생성
- 에러 없음

---

### TC-DB-BAK-002: 데이터베이스 복구

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-DB-BAK-002 |
| 테스트명 | PostgreSQL 백업 복구 |
| 우선순위 | High |
| 사전조건 | 백업 파일 존재 |

**테스트 절차:**
```bash
# 기존 데이터베이스 삭제 후 재생성
docker exec pbt_vlm_ocr-postgres-1 dropdb -U postgres pbt_ocr
docker exec pbt_vlm_ocr-postgres-1 createdb -U postgres pbt_ocr

# 복구
cat backup.sql | docker exec -i pbt_vlm_ocr-postgres-1 psql -U postgres pbt_ocr
```

**예상 결과:**
- 데이터 완전 복구
- 모든 테이블/레코드 정상

---

## 11. 테스트 데이터 정리 스크립트

```sql
-- 테스트 데이터 정리
DELETE FROM blocks WHERE page_id IN (SELECT id FROM pages WHERE document_id IN (SELECT id FROM documents WHERE original_filename LIKE 'test%'));
DELETE FROM pages WHERE document_id IN (SELECT id FROM documents WHERE original_filename LIKE 'test%');
DELETE FROM documents WHERE original_filename LIKE 'test%';

-- 시퀀스 리셋 (선택)
-- ALTER SEQUENCE documents_id_seq RESTART WITH 1;
```

---

## 12. 자동화 테스트 스크립트

```bash
#!/bin/bash
# Database 테스트 실행 스크립트

echo "=== Database 테스트 시작 ==="

# 1. 연결 테스트
echo "[1/5] PostgreSQL 연결 테스트..."
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "SELECT 1 as connection_test;"

# 2. 스키마 확인
echo "[2/5] 스키마 확인..."
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
"

# 3. 레코드 카운트
echo "[3/5] 레코드 카운트..."
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT
  (SELECT COUNT(*) FROM documents) as documents,
  (SELECT COUNT(*) FROM pages) as pages,
  (SELECT COUNT(*) FROM blocks) as blocks;
"

# 4. 쿼리 성능
echo "[4/5] 쿼리 성능 테스트..."
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
EXPLAIN ANALYZE SELECT * FROM documents ORDER BY created_at DESC LIMIT 10;
"

# 5. 인덱스 확인
echo "[5/5] 인덱스 확인..."
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -d pbt_ocr -c "
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';
"

echo "=== Database 테스트 완료 ==="
```
