# PBT Docker Registry 사용 매뉴얼

## 1. 개요

PBT Docker Registry는 192.168.1.x 네트워크 내에서 Docker 이미지를 중앙 관리하기 위한 프라이빗 레지스트리 서버입니다.

### 서버 정보

| 항목 | 값 |
|------|-----|
| Registry API | `http://192.168.1.39:5000` |
| Registry UI | `http://192.168.1.39:8090` |
| 데이터 저장 경로 | `/home/magic/work/Docker-Registry/data` |

---

## 2. 클라이언트 설정 (최초 1회)

Registry 서버가 HTTPS가 아닌 HTTP를 사용하므로, Docker 클라이언트에서 insecure-registry 설정이 필요합니다.

### Linux

```bash
# /etc/docker/daemon.json 파일 편집
sudo vi /etc/docker/daemon.json
```

다음 내용을 추가합니다:

```json
{
  "insecure-registries": ["192.168.1.39:5000"]
}
```

기존에 다른 설정이 있는 경우:

```json
{
  "기존설정": "값",
  "insecure-registries": ["192.168.1.39:5000"]
}
```

설정 후 Docker 재시작:

```bash
sudo systemctl restart docker
```

### Windows (Docker Desktop)

1. Docker Desktop 실행
2. Settings (설정) > Docker Engine 클릭
3. JSON 설정에 다음 추가:
   ```json
   {
     "insecure-registries": ["192.168.1.39:5000"]
   }
   ```
4. Apply & Restart 클릭

### macOS (Docker Desktop)

1. Docker Desktop 실행
2. Preferences > Docker Engine 클릭
3. JSON 설정에 `insecure-registries` 추가
4. Apply & Restart 클릭

---

## 3. 이미지 Push (업로드)

로컬에 있는 Docker 이미지를 Registry 서버에 업로드하는 방법입니다.

### 기본 형식

```bash
# 1. 이미지에 Registry 태그 추가
docker tag <로컬이미지>:<태그> 192.168.1.39:5000/<이미지명>:<태그>

# 2. Registry에 Push
docker push 192.168.1.39:5000/<이미지명>:<태그>
```

### 예시

```bash
# PBT_OCR 이미지 Push
docker tag pbt_ocr:latest 192.168.1.39:5000/pbt_ocr:v1.0
docker push 192.168.1.39:5000/pbt_ocr:v1.0

# ZImage 이미지 Push
docker tag zimage-backend:latest 192.168.1.39:5000/zimage-backend:v2.1
docker push 192.168.1.39:5000/zimage-backend:v2.1

# 여러 태그로 Push (latest + 버전)
docker tag myapp:latest 192.168.1.39:5000/myapp:latest
docker tag myapp:latest 192.168.1.39:5000/myapp:v1.0.0
docker push 192.168.1.39:5000/myapp:latest
docker push 192.168.1.39:5000/myapp:v1.0.0
```

---

## 4. 이미지 Pull (다운로드)

Registry 서버에서 이미지를 다운로드하는 방법입니다.

### 기본 형식

```bash
docker pull 192.168.1.39:5000/<이미지명>:<태그>
```

### 예시

```bash
# 특정 버전 Pull
docker pull 192.168.1.39:5000/pbt_ocr:v1.0

# latest 태그 Pull
docker pull 192.168.1.39:5000/zimage-backend:latest
```

---

## 5. 웹 UI 사용법

브라우저에서 `http://192.168.1.39:8090` 접속

### 주요 기능

| 기능 | 설명 |
|------|------|
| 이미지 목록 | 메인 화면에서 등록된 모든 이미지 확인 |
| 태그 목록 | 이미지 클릭 시 해당 이미지의 모든 태그(버전) 확인 |
| 이미지 삭제 | 태그 옆 휴지통 아이콘 클릭하여 삭제 |
| 상세 정보 | 이미지 크기, 다이제스트, 레이어 정보 확인 |

### 화면 구성

```
+------------------------------------------+
|  PBT Docker Registry                     |
+------------------------------------------+
|  [이미지 검색...]                         |
+------------------------------------------+
|  pbt_ocr                    3 tags       |
|  zimage-backend             2 tags       |
|  zimage-frontend            2 tags       |
|  pbtax-gateway              1 tag        |
+------------------------------------------+
```

---

## 6. API를 통한 이미지 조회

### 저장된 이미지 목록 조회

```bash
curl http://192.168.1.39:5000/v2/_catalog
```

응답 예시:
```json
{
  "repositories": ["pbt_ocr", "zimage-backend", "zimage-frontend"]
}
```

### 특정 이미지의 태그 목록 조회

```bash
curl http://192.168.1.39:5000/v2/<이미지명>/tags/list
```

예시:
```bash
curl http://192.168.1.39:5000/v2/pbt_ocr/tags/list
```

응답 예시:
```json
{
  "name": "pbt_ocr",
  "tags": ["v1.0", "v1.1", "latest"]
}
```

---

## 7. 이미지 삭제

### 웹 UI에서 삭제 (권장)

1. `http://192.168.1.39:8090` 접속
2. 삭제할 이미지 클릭
3. 삭제할 태그 옆 휴지통 아이콘 클릭
4. 확인 버튼 클릭

### API로 삭제

```bash
# 1. 이미지 다이제스트 확인
curl -I -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  http://192.168.1.39:5000/v2/<이미지명>/manifests/<태그>

# 2. Docker-Content-Digest 헤더 값으로 삭제
curl -X DELETE \
  http://192.168.1.39:5000/v2/<이미지명>/manifests/<다이제스트>
```

### 삭제 후 디스크 정리 (Garbage Collection)

이미지 삭제 후 실제 디스크 공간을 확보하려면:

```bash
# Registry 서버에서 실행
docker exec docker-registry bin/registry garbage-collect /etc/docker/registry/config.yml
```

---

## 8. 서버 관리

### systemd 서비스 등록 (서버 부팅 시 자동 시작)

서버 재부팅 시 자동으로 Registry가 시작되도록 systemd 서비스를 등록합니다.

```bash
# 서비스 파일 복사
sudo cp /home/magic/work/Docker-Registry/docker-registry.service /etc/systemd/system/

# systemd 데몬 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable docker-registry.service

# 서비스 시작
sudo systemctl start docker-registry.service
```

### systemd 서비스 명령어

```bash
# 서비스 상태 확인
sudo systemctl status docker-registry

# 서비스 시작
sudo systemctl start docker-registry

# 서비스 중지
sudo systemctl stop docker-registry

# 서비스 재시작
sudo systemctl restart docker-registry

# 부팅 시 자동 시작 해제
sudo systemctl disable docker-registry
```

### Docker Compose로 직접 관리

systemd 없이 직접 관리할 경우:

```bash
cd /home/magic/work/Docker-Registry
docker compose ps
```

### 서비스 시작/중지/재시작

```bash
# 시작
docker compose up -d

# 중지
docker compose down

# 재시작
docker compose restart
```

### 헬스체크 상태 확인

```bash
# 컨테이너 헬스 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}" | grep registry
```

정상 상태 예시:
```
docker-registry-ui       Up 5 minutes (healthy)
docker-registry          Up 5 minutes (healthy)
```

### 로그 확인

```bash
# 전체 로그
docker compose logs

# 실시간 로그 확인
docker compose logs -f

# Registry 로그만 확인
docker compose logs registry

# UI 로그만 확인
docker compose logs registry-ui
```

### 디스크 사용량 확인

```bash
du -sh /home/magic/work/Docker-Registry/data
```

---

## 9. 문제 해결

### Push/Pull 시 "server gave HTTP response to HTTPS client" 오류

**원인**: 클라이언트에 insecure-registry 설정이 되어 있지 않음

**해결**: [2. 클라이언트 설정](#2-클라이언트-설정-최초-1회) 참고하여 설정 후 Docker 재시작

### Push 시 "denied: requested access to the resource is denied" 오류

**원인**: 이미지 태그가 올바르지 않음

**해결**: 이미지 태그에 `192.168.1.39:5000/` 접두사가 포함되어 있는지 확인

```bash
# 올바른 형식
docker tag myimage:latest 192.168.1.39:5000/myimage:latest
docker push 192.168.1.39:5000/myimage:latest
```

### 웹 UI에서 이미지가 보이지 않음

**원인**: CORS 설정 문제 또는 Registry와 UI 간 통신 문제

**해결**:
```bash
# 서비스 재시작
cd /home/magic/work/Docker-Registry
docker compose restart
```

### Registry 서버 접속 불가

**확인 사항**:
```bash
# 1. 컨테이너 실행 상태 확인
docker ps | grep registry

# 2. 포트 리스닝 확인
netstat -tlnp | grep 5000

# 3. 방화벽 확인
sudo ufw status
```

---

## 10. 권장 이미지 네이밍 규칙

일관된 관리를 위해 다음 네이밍 규칙을 권장합니다:

### 형식

```
192.168.1.39:5000/<프로젝트명>/<서비스명>:<버전>
```

### 예시

| 이미지 | 설명 |
|--------|------|
| `192.168.1.39:5000/pbt/ocr:v1.0` | PBT OCR 서비스 v1.0 |
| `192.168.1.39:5000/zimage/backend:v2.1` | ZImage 백엔드 v2.1 |
| `192.168.1.39:5000/zimage/frontend:latest` | ZImage 프론트엔드 최신 |
| `192.168.1.39:5000/pbtax/gateway:v1.0` | PBTax 게이트웨이 v1.0 |

### 버전 태그 규칙

- `latest`: 최신 안정 버전
- `v1.0.0`: 정식 릴리스 버전 (Semantic Versioning)
- `dev`: 개발 버전
- `staging`: 스테이징 버전

---

## 부록: 자주 사용하는 명령어 모음

```bash
# 이미지 태깅 및 Push
docker tag <이미지>:<태그> 192.168.1.39:5000/<이미지>:<태그>
docker push 192.168.1.39:5000/<이미지>:<태그>

# 이미지 Pull
docker pull 192.168.1.39:5000/<이미지>:<태그>

# 저장된 이미지 목록
curl http://192.168.1.39:5000/v2/_catalog

# 특정 이미지 태그 목록
curl http://192.168.1.39:5000/v2/<이미지>/tags/list

# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```
