# 보안 테스트 케이스

## 1. 개요

시스템 보안에 대한 테스트 케이스입니다. 인증/인가, 입력 검증, CORS, 데이터 보호를 검증합니다.

---

## 2. OWASP Top 10 기반 테스트

### 2.1 인젝션 공격

#### TC-SEC-INJ-001: SQL 인젝션 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-INJ-001 |
| 테스트명 | SQL 인젝션 취약점 테스트 |
| 우선순위 | Critical |
| 사전조건 | - |

**테스트 절차:**
```bash
# 검색 파라미터에 SQL 인젝션 시도
curl "http://localhost:8000/api/v1/documents/?search='; DROP TABLE documents; --"
curl "http://localhost:8000/api/v1/documents/?search=1' OR '1'='1"
curl "http://localhost:8000/api/v1/documents/1 OR 1=1"
```

**예상 결과:**
- 에러 또는 정상 응답 (주입된 SQL 실행 안됨)
- 파라미터 이스케이프 처리
- SQLAlchemy ORM 보호

---

#### TC-SEC-INJ-002: NoSQL 인젝션 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-INJ-002 |
| 테스트명 | NoSQL 인젝션 취약점 테스트 |
| 우선순위 | Medium |
| 사전조건 | Qdrant 벡터 DB 사용 시 |

**테스트 절차:**
```bash
# JSON 페이로드에 인젝션 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Content-Type: application/json" \
  -d '{"$gt": "", "ocr_mode": "FAST"}'
```

**예상 결과:**
- 입력 검증으로 차단
- 에러 응답

---

#### TC-SEC-INJ-003: 명령어 인젝션 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-INJ-003 |
| 테스트명 | OS 명령어 인젝션 테스트 |
| 우선순위 | Critical |
| 사전조건 | - |

**테스트 절차:**
```bash
# 파일명에 명령어 인젝션 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@test.pdf;filename=\"; rm -rf /; #.pdf\""

# 파라미터에 명령어 인젝션
curl "http://localhost:8000/api/v1/documents/?id=1;ls"
```

**예상 결과:**
- 파일명 새니타이즈
- 명령 실행 안됨

---

### 2.2 인증 및 세션 관리

#### TC-SEC-AUTH-001: 인증 우회 시도

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-AUTH-001 |
| 테스트명 | 인증 없이 보호된 리소스 접근 |
| 우선순위 | Critical |
| 사전조건 | 인증이 필요한 엔드포인트 존재 시 |

**테스트 절차:**
```bash
# 인증 헤더 없이 요청
curl http://localhost:8000/api/v1/admin/settings

# 잘못된 토큰으로 요청
curl -H "Authorization: Bearer invalid_token" http://localhost:8000/api/v1/documents/
```

**예상 결과:**
- 401 Unauthorized 또는 403 Forbidden
- 현재 시스템: 인증 없이 공개 API (개발 환경)

---

#### TC-SEC-AUTH-002: 세션 고정 공격 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-AUTH-002 |
| 테스트명 | 세션 고정 공격 취약점 |
| 우선순위 | High |
| 사전조건 | 세션 기반 인증 사용 시 |

**테스트 절차:**
- 세션 ID 고정 후 인증 시도
- 인증 후 세션 ID 변경 확인

**예상 결과:**
- 인증 후 새 세션 ID 발급
- (현재: 세션 미사용)

---

### 2.3 민감 데이터 노출

#### TC-SEC-DATA-001: API 응답에서 민감 정보 노출

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-DATA-001 |
| 테스트명 | API 응답 민감 정보 검사 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# API 응답 분석
curl http://localhost:8000/api/v1/documents/ | jq

# 에러 응답 분석
curl http://localhost:8000/api/v1/documents/99999
```

**검사 항목:**
- 내부 경로 노출 여부
- 스택 트레이스 노출 여부
- DB 연결 정보 노출 여부

**예상 결과:**
- 민감 정보 미포함
- 일반적인 에러 메시지

---

#### TC-SEC-DATA-002: 파일 내용 노출 검사

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-DATA-002 |
| 테스트명 | 업로드된 파일 직접 접근 차단 |
| 우선순위 | High |
| 사전조건 | 업로드된 파일 존재 |

**테스트 절차:**
```bash
# MinIO 직접 접근 시도
curl http://localhost:9000/pbt-ocr-documents/documents/1/original.pdf

# 경로 조작 시도
curl http://localhost:8000/api/v1/files/documents/../../../etc/passwd
```

**예상 결과:**
- MinIO: 인증 필요
- 경로 조작: 차단

---

### 2.4 XSS (Cross-Site Scripting)

#### TC-SEC-XSS-001: 저장형 XSS 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-XSS-001 |
| 테스트명 | 파일명에 XSS 페이로드 저장 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# XSS 페이로드가 포함된 파일명으로 업로드
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@test.pdf;filename=\"<script>alert('XSS')</script>.pdf\""

# 목록 조회 시 이스케이프 확인
curl http://localhost:8000/api/v1/documents/
```

**예상 결과:**
- 파일명 새니타이즈 또는 이스케이프
- HTML 인코딩

---

#### TC-SEC-XSS-002: 반사형 XSS 테스트

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-XSS-002 |
| 테스트명 | 검색 파라미터 XSS |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# XSS 페이로드 주입
curl "http://localhost:8000/api/v1/documents/?search=<script>alert('XSS')</script>"
```

**예상 결과:**
- Content-Type: application/json (HTML 아님)
- 이스케이프 처리

---

### 2.5 CORS 및 보안 헤더

#### TC-SEC-CORS-001: CORS 설정 검증

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-CORS-001 |
| 테스트명 | CORS 헤더 확인 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# Preflight 요청
curl -v -X OPTIONS http://localhost:8000/api/v1/documents/ \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST"

# 실제 요청
curl -v http://localhost:8000/api/v1/documents/ \
  -H "Origin: http://localhost:3000"
```

**예상 결과:**
- Access-Control-Allow-Origin 헤더 확인
- 현재: CORS_ORIGINS = ["*"] (개발 환경)
- 프로덕션: 특정 도메인만 허용 권장

---

#### TC-SEC-CORS-002: 보안 헤더 확인

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-CORS-002 |
| 테스트명 | HTTP 보안 헤더 검사 |
| 우선순위 | Medium |
| 사전조건 | - |

**테스트 절차:**
```bash
curl -I http://localhost:8000/api/v1/documents/
```

**검사 헤더:**
| 헤더 | 권장 값 | 설명 |
|------|--------|------|
| X-Content-Type-Options | nosniff | MIME 스니핑 방지 |
| X-Frame-Options | DENY | 클릭재킹 방지 |
| X-XSS-Protection | 1; mode=block | XSS 필터 |
| Strict-Transport-Security | max-age=31536000 | HTTPS 강제 |
| Content-Security-Policy | default-src 'self' | CSP |

---

### 2.6 파일 업로드 보안

#### TC-SEC-FILE-001: 악성 파일 업로드 차단

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-FILE-001 |
| 테스트명 | 허용되지 않은 파일 형식 업로드 |
| 우선순위 | Critical |
| 사전조건 | - |

**테스트 절차:**
```bash
# 실행 파일 업로드 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@malware.exe"

# PHP 파일 업로드 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@shell.php"

# 이중 확장자 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@malware.pdf.exe"
```

**예상 결과:**
- 400 Bad Request
- "Unsupported file type" 에러

---

#### TC-SEC-FILE-002: 파일 크기 제한

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-FILE-002 |
| 테스트명 | 대용량 파일 업로드 제한 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# 100MB 파일 생성
dd if=/dev/zero of=/tmp/large.pdf bs=1M count=100

# 업로드 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/tmp/large.pdf"
```

**예상 결과:**
- 파일 크기 제한 에러
- 413 Payload Too Large

---

#### TC-SEC-FILE-003: 디렉토리 트래버설 방지

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-FILE-003 |
| 테스트명 | 경로 조작 공격 차단 |
| 우선순위 | Critical |
| 사전조건 | - |

**테스트 절차:**
```bash
# 경로 조작 시도
curl http://localhost:8000/api/v1/files/documents/../../../etc/passwd/download
curl http://localhost:8000/api/v1/files/documents/1/pages/..%2F..%2F..%2Fetc%2Fpasswd/image
```

**예상 결과:**
- 404 Not Found 또는 400 Bad Request
- 시스템 파일 접근 차단

---

### 2.7 Rate Limiting

#### TC-SEC-RATE-001: API 요청 속도 제한

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-RATE-001 |
| 테스트명 | API Rate Limiting |
| 우선순위 | Medium |
| 사전조건 | Rate Limit 설정 시 |

**테스트 절차:**
```bash
# 빠른 연속 요청
for i in {1..100}; do
  curl -s http://localhost:8000/api/v1/documents/ &
done
wait
```

**예상 결과:**
- 429 Too Many Requests (Rate Limit 설정 시)
- 현재: Rate Limit 미설정 (개발 환경)

---

#### TC-SEC-RATE-002: 업로드 속도 제한

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-RATE-002 |
| 테스트명 | 파일 업로드 Rate Limiting |
| 우선순위 | Medium |
| 사전조건 | - |

**테스트 절차:**
```bash
# 연속 업로드
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/api/v1/documents/ \
    -F "file=@/data/sample.pdf" &
done
wait
```

**예상 결과:**
- 업로드 제한 동작 (설정 시)

---

### 2.8 DoS 방어

#### TC-SEC-DOS-001: 대용량 요청 처리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-DOS-001 |
| 테스트명 | 대용량 JSON 페이로드 처리 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# 대용량 JSON 생성
python -c "print('{\"data\": \"' + 'A' * 10000000 + '\"}')" > /tmp/large.json

# 전송 시도
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Content-Type: application/json" \
  -d @/tmp/large.json
```

**예상 결과:**
- 요청 크기 제한
- 413 Payload Too Large

---

#### TC-SEC-DOS-002: Slowloris 공격 대응

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-DOS-002 |
| 테스트명 | 느린 HTTP 요청 처리 |
| 우선순위 | Medium |
| 사전조건 | - |

**테스트 절차:**
- 느린 속도로 HTTP 헤더 전송
- 연결 타임아웃 확인

**예상 결과:**
- 연결 타임아웃 동작
- 리소스 해제

---

## 3. 인프라 보안

### TC-SEC-INFRA-001: 컨테이너 권한

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-INFRA-001 |
| 테스트명 | Docker 컨테이너 권한 확인 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# 컨테이너 사용자 확인
docker exec pbt_vlm_ocr-backend-1 id

# 권한 확인
docker inspect pbt_vlm_ocr-backend-1 --format='{{.HostConfig.Privileged}}'
```

**예상 결과:**
- root가 아닌 사용자 권장
- Privileged: false

---

### TC-SEC-INFRA-002: 네트워크 격리

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-INFRA-002 |
| 테스트명 | Docker 네트워크 격리 확인 |
| 우선순위 | Medium |
| 사전조건 | - |

**테스트 절차:**
```bash
# 네트워크 확인
docker network inspect pbt-network

# 외부 접근 포트 확인
docker ps --format "{{.Ports}}"
```

**예상 결과:**
- 내부 서비스 (postgres, redis) 외부 노출 최소화
- 필요한 포트만 공개

---

### TC-SEC-INFRA-003: 환경 변수 보안

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-INFRA-003 |
| 테스트명 | 민감 정보 환경 변수 관리 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# 환경 변수 확인
docker exec pbt_vlm_ocr-backend-1 env | grep -E "(PASSWORD|SECRET|KEY)"
```

**예상 결과:**
- 민감 정보 암호화 또는 시크릿 관리
- 프로덕션: .env 파일 분리, 시크릿 매니저 사용

---

## 4. 데이터 보호

### TC-SEC-PROT-001: 데이터베이스 암호화

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-PROT-001 |
| 테스트명 | PostgreSQL 연결 암호화 |
| 우선순위 | High |
| 사전조건 | SSL 설정 시 |

**테스트 절차:**
```bash
# SSL 연결 확인
docker exec pbt_vlm_ocr-postgres-1 psql -U postgres -c "SHOW ssl;"
```

**예상 결과:**
- 프로덕션: SSL 활성화
- 개발: off (허용)

---

### TC-SEC-PROT-002: 저장 데이터 암호화

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-PROT-002 |
| 테스트명 | MinIO 저장 데이터 암호화 |
| 우선순위 | Medium |
| 사전조건 | 암호화 설정 시 |

**테스트 절차:**
- MinIO 서버 측 암호화 (SSE) 확인
- KMS 연동 확인

**예상 결과:**
- 프로덕션: SSE 활성화 권장

---

## 5. 로깅 및 모니터링

### TC-SEC-LOG-001: 보안 이벤트 로깅

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-LOG-001 |
| 테스트명 | 보안 관련 로그 기록 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# 잘못된 요청 후 로그 확인
curl http://localhost:8000/api/v1/documents/invalid_id
docker logs pbt_vlm_ocr-backend-1 --tail 20
```

**예상 결과:**
- 요청 정보 로깅
- IP 주소, 타임스탬프, 에러 코드

---

### TC-SEC-LOG-002: 민감 정보 로그 제외

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-LOG-002 |
| 테스트명 | 로그에서 민감 정보 제외 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# 로그 검사
docker logs pbt_vlm_ocr-backend-1 | grep -E "(password|secret|key)" -i
```

**예상 결과:**
- 비밀번호, API 키 등 미노출
- 마스킹 처리

---

## 6. 취약점 스캔

### TC-SEC-SCAN-001: 의존성 취약점 스캔

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-SCAN-001 |
| 테스트명 | Python 패키지 취약점 스캔 |
| 우선순위 | High |
| 사전조건 | - |

**테스트 절차:**
```bash
# pip-audit 사용
docker exec pbt_vlm_ocr-backend-1 pip install pip-audit
docker exec pbt_vlm_ocr-backend-1 pip-audit

# safety 사용
pip install safety
safety check -r backend/requirements.txt
```

**예상 결과:**
- Critical/High 취약점 없음

---

### TC-SEC-SCAN-002: Docker 이미지 취약점 스캔

| 항목 | 내용 |
|------|------|
| 테스트 ID | TC-SEC-SCAN-002 |
| 테스트명 | Docker 이미지 보안 스캔 |
| 우선순위 | Medium |
| 사전조건 | trivy 설치 |

**테스트 절차:**
```bash
# Trivy 스캔
trivy image pbt_vlm_ocr-backend:latest
trivy image pbt_vlm_ocr-frontend:latest
```

**예상 결과:**
- Critical 취약점 없음
- High 취약점 최소화

---

## 7. 보안 체크리스트

### 개발 환경 체크리스트

| 항목 | 상태 | 비고 |
|------|------|------|
| CORS 설정 | ⚠️ | 현재 "*" (개발용) |
| 인증 없음 | ⚠️ | 공개 API (개발용) |
| 파일 형식 검증 | ✅ | PDF, 이미지만 허용 |
| SQL 인젝션 방지 | ✅ | SQLAlchemy ORM |
| XSS 방지 | ✅ | JSON 응답 |
| HTTPS | ❌ | HTTP 사용 (개발용) |

### 프로덕션 권장 사항

| 항목 | 권장 |
|------|------|
| CORS | 특정 도메인만 허용 |
| 인증 | JWT 또는 API Key |
| HTTPS | TLS 1.2+ 필수 |
| Rate Limiting | 요청 수 제한 |
| WAF | 웹 애플리케이션 방화벽 |
| 로깅 | 중앙 집중 로그 관리 |

---

## 8. 자동화 보안 테스트 스크립트

```bash
#!/bin/bash
# 보안 테스트 실행 스크립트

echo "=== PBT VLM OCR 보안 테스트 시작 ==="

RESULTS=()

# 1. SQL 인젝션 테스트
echo "[1/7] SQL 인젝션 테스트..."
RESPONSE=$(curl -s "http://localhost:8000/api/v1/documents/?search='; DROP TABLE--")
if [[ "$RESPONSE" != *"error"* ]] || [[ "$RESPONSE" == *"items"* ]]; then
  RESULTS+=("SQL 인젝션: PASS")
else
  RESULTS+=("SQL 인젝션: CHECK")
fi

# 2. XSS 테스트
echo "[2/7] XSS 테스트..."
RESPONSE=$(curl -s "http://localhost:8000/api/v1/documents/?search=<script>alert(1)</script>")
CONTENT_TYPE=$(curl -sI "http://localhost:8000/api/v1/documents/" | grep -i "content-type")
if [[ "$CONTENT_TYPE" == *"application/json"* ]]; then
  RESULTS+=("XSS 방지: PASS (JSON Content-Type)")
else
  RESULTS+=("XSS 방지: CHECK")
fi

# 3. 파일 업로드 테스트
echo "[3/7] 악성 파일 업로드 테스트..."
echo "malicious content" > /tmp/test.exe
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/ \
  -F "file=@/tmp/test.exe")
if [[ "$RESPONSE" == *"error"* ]] || [[ "$RESPONSE" == *"Unsupported"* ]]; then
  RESULTS+=("파일 형식 검증: PASS")
else
  RESULTS+=("파일 형식 검증: FAIL")
fi
rm /tmp/test.exe

# 4. 경로 조작 테스트
echo "[4/7] 경로 조작 테스트..."
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
  "http://localhost:8000/api/v1/files/documents/../../../etc/passwd/download")
if [ "$HTTP_CODE" -eq 404 ] || [ "$HTTP_CODE" -eq 400 ]; then
  RESULTS+=("경로 조작 방지: PASS")
else
  RESULTS+=("경로 조작 방지: CHECK (HTTP $HTTP_CODE)")
fi

# 5. CORS 헤더 확인
echo "[5/7] CORS 설정 확인..."
CORS_HEADER=$(curl -sI -X OPTIONS http://localhost:8000/api/v1/documents/ \
  -H "Origin: http://evil.com" | grep -i "access-control-allow-origin")
echo "CORS: $CORS_HEADER"
RESULTS+=("CORS: 수동 확인 필요")

# 6. 보안 헤더 확인
echo "[6/7] 보안 헤더 확인..."
HEADERS=$(curl -sI http://localhost:8000/api/v1/documents/)
echo "$HEADERS" | grep -E "(X-Content-Type|X-Frame|X-XSS|Strict-Transport)" || echo "보안 헤더 미설정"
RESULTS+=("보안 헤더: 수동 확인 필요")

# 7. 환경 변수 확인
echo "[7/7] 민감 정보 노출 확인..."
API_RESPONSE=$(curl -s http://localhost:8000/api/v1/documents/999999)
if [[ "$API_RESPONSE" != *"postgres"* ]] && [[ "$API_RESPONSE" != *"password"* ]]; then
  RESULTS+=("민감 정보 노출: PASS")
else
  RESULTS+=("민감 정보 노출: FAIL")
fi

# 결과 출력
echo ""
echo "=== 보안 테스트 결과 요약 ==="
for result in "${RESULTS[@]}"; do
  echo "  - $result"
done
echo "============================="
echo ""
echo "⚠️ 주의: 이 스크립트는 기본적인 테스트만 수행합니다."
echo "프로덕션 환경에서는 전문 보안 감사를 권장합니다."
```

---

## 9. OWASP ZAP 자동 스캔

```bash
# OWASP ZAP Docker를 사용한 자동 스캔
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://host.docker.internal:8000/api/v1/ \
  -r zap_report.html
```

---

## 10. 보안 테스트 체크리스트

| 분류 | 테스트 항목 | 통과 |
|------|-------------|------|
| 인젝션 | SQL 인젝션 | [ ] |
| 인젝션 | NoSQL 인젝션 | [ ] |
| 인젝션 | 명령어 인젝션 | [ ] |
| 인증 | 인증 우회 | [ ] |
| 데이터 | 민감 정보 노출 | [ ] |
| XSS | 저장형 XSS | [ ] |
| XSS | 반사형 XSS | [ ] |
| CORS | CORS 설정 | [ ] |
| 헤더 | 보안 헤더 | [ ] |
| 파일 | 악성 파일 업로드 | [ ] |
| 파일 | 파일 크기 제한 | [ ] |
| 파일 | 경로 조작 | [ ] |
| DoS | Rate Limiting | [ ] |
| DoS | 대용량 요청 | [ ] |
| 인프라 | 컨테이너 권한 | [ ] |
| 인프라 | 네트워크 격리 | [ ] |
| 로깅 | 보안 이벤트 로깅 | [ ] |
| 의존성 | 취약점 스캔 | [ ] |
