"""
시스템 상태 모니터링 서비스
"""
import time
import asyncio
from datetime import datetime
from typing import List, Optional

import httpx
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.system import (
    ServiceStatus,
    WorkerQueueStatus,
    GPUStatus,
    StorageStatus,
    SystemStatusResponse,
)


async def check_database(db: Session) -> ServiceStatus:
    """PostgreSQL 데이터베이스 상태 확인"""
    try:
        start = time.time()
        db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return ServiceStatus(
            name="PostgreSQL",
            status="healthy",
            latency_ms=round(latency, 2),
            message="연결 정상",
        )
    except Exception as e:
        return ServiceStatus(
            name="PostgreSQL",
            status="unhealthy",
            message=f"연결 실패: {str(e)}",
        )


async def check_redis() -> ServiceStatus:
    """Redis 상태 확인"""
    try:
        start = time.time()
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        latency = (time.time() - start) * 1000
        info = r.info()
        return ServiceStatus(
            name="Redis",
            status="healthy",
            latency_ms=round(latency, 2),
            message="연결 정상",
            details={
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
            },
        )
    except Exception as e:
        return ServiceStatus(
            name="Redis",
            status="unhealthy",
            message=f"연결 실패: {str(e)}",
        )


async def check_minio() -> ServiceStatus:
    """MinIO 상태 확인"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{settings.MINIO_ENDPOINT}/minio/health/live")
            latency = (time.time() - start) * 1000
            if response.status_code == 200:
                return ServiceStatus(
                    name="MinIO",
                    status="healthy",
                    latency_ms=round(latency, 2),
                    message="연결 정상",
                )
            else:
                return ServiceStatus(
                    name="MinIO",
                    status="unhealthy",
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                )
    except Exception as e:
        return ServiceStatus(
            name="MinIO",
            status="unhealthy",
            message=f"연결 실패: {str(e)}",
        )


async def check_qdrant() -> ServiceStatus:
    """Qdrant 상태 확인"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/healthz"
            )
            latency = (time.time() - start) * 1000
            if response.status_code == 200:
                return ServiceStatus(
                    name="Qdrant",
                    status="healthy",
                    latency_ms=round(latency, 2),
                    message="연결 정상",
                )
            else:
                return ServiceStatus(
                    name="Qdrant",
                    status="unhealthy",
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                )
    except Exception as e:
        return ServiceStatus(
            name="Qdrant",
            status="unhealthy",
            message=f"연결 실패: {str(e)}",
        )


async def check_vlm(db: Session) -> ServiceStatus:
    """VLM (vLLM) 서버 상태 확인 - DB 설정 사용"""
    try:
        # DB에서 VLM 설정 조회
        from app.models.settings import Settings as SettingsModel
        db_settings = db.query(SettingsModel).filter(SettingsModel.id == 1).first()

        vlm_endpoint = db_settings.vlm_endpoint_url if db_settings and db_settings.vlm_endpoint_url else settings.VLM_API_BASE

        if not vlm_endpoint:
            return ServiceStatus(
                name="VLM (GPU)",
                status="unhealthy",
                message="VLM 엔드포인트가 설정되지 않음",
            )

        start = time.time()
        # VLM API 베이스에서 /health 또는 /v1/models 확인
        vlm_base = vlm_endpoint.rstrip('/v1').rstrip('/')
        async with httpx.AsyncClient(timeout=10.0) as client:
            # health 엔드포인트 시도
            try:
                response = await client.get(f"{vlm_base}/health")
                latency = (time.time() - start) * 1000
                if response.status_code == 200:
                    return ServiceStatus(
                        name="VLM (GPU)",
                        status="healthy",
                        latency_ms=round(latency, 2),
                        message="GPU 서버 정상",
                    )
            except:
                pass

            # /v1/models 엔드포인트 시도
            response = await client.get(f"{vlm_base}/v1/models")
            latency = (time.time() - start) * 1000
            if response.status_code == 200:
                data = response.json()
                models = [m.get("id") for m in data.get("data", [])]
                return ServiceStatus(
                    name="VLM (GPU)",
                    status="healthy",
                    latency_ms=round(latency, 2),
                    message="GPU 서버 정상",
                    details={"available_models": models},
                )
            else:
                return ServiceStatus(
                    name="VLM (GPU)",
                    status="unhealthy",
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                )
    except httpx.TimeoutException:
        return ServiceStatus(
            name="VLM (GPU)",
            status="unhealthy",
            message="연결 시간 초과",
        )
    except Exception as e:
        return ServiceStatus(
            name="VLM (GPU)",
            status="unhealthy",
            message=f"연결 실패: {str(e)}",
        )


async def get_worker_status() -> List[WorkerQueueStatus]:
    """Celery 워커 상태 확인"""
    workers = []

    try:
        r = redis.from_url(settings.REDIS_URL)

        # 각 큐별 상태 확인
        queues = [
            ("Fast OCR", "fast_ocr"),
            ("Accurate OCR", "accurate_ocr"),
            ("Precision OCR", "precision_ocr"),
        ]

        for name, queue_name in queues:
            try:
                # 큐의 대기 중인 작업 수 확인
                queue_length = r.llen(queue_name)

                # 워커 상태 확인 (celery inspect를 사용할 수도 있지만, 간단히 큐 길이로 판단)
                status = "active" if queue_length > 0 else "idle"

                workers.append(WorkerQueueStatus(
                    name=name,
                    queue_name=queue_name,
                    active_tasks=queue_length,
                    reserved_tasks=0,
                    workers=1,  # docker-compose에서 설정된 기본값
                    status=status,
                ))
            except Exception:
                workers.append(WorkerQueueStatus(
                    name=name,
                    queue_name=queue_name,
                    active_tasks=0,
                    reserved_tasks=0,
                    workers=0,
                    status="offline",
                ))
    except Exception:
        # Redis 연결 실패 시 모든 워커를 offline으로 표시
        for name, queue_name in [
            ("Fast OCR", "fast_ocr"),
            ("Accurate OCR", "accurate_ocr"),
            ("Precision OCR", "precision_ocr"),
        ]:
            workers.append(WorkerQueueStatus(
                name=name,
                queue_name=queue_name,
                active_tasks=0,
                reserved_tasks=0,
                workers=0,
                status="offline",
            ))

    return workers


async def get_gpu_status() -> Optional[List[GPUStatus]]:
    """GPU 상태 확인 (VLM 서버를 통해)"""
    try:
        vlm_base = settings.VLM_API_BASE.rstrip('/v1').rstrip('/')
        async with httpx.AsyncClient(timeout=5.0) as client:
            # vLLM의 metrics 또는 custom GPU endpoint 확인
            # 기본적으로 vLLM은 GPU 정보를 직접 노출하지 않으므로
            # 서버가 응답하면 GPU가 사용 가능한 것으로 간주
            response = await client.get(f"{vlm_base}/health")
            if response.status_code == 200:
                return [GPUStatus(
                    index=0,
                    name="NVIDIA GPU (vLLM)",
                    memory_used_mb=0,
                    memory_total_mb=0,
                    memory_percent=0,
                    gpu_utilization=0,
                    status="available",
                )]
    except:
        pass

    return None


async def get_storage_status() -> Optional[StorageStatus]:
    """스토리지 상태 확인"""
    try:
        # MinIO 버킷 정보 조회는 복잡하므로 간단히 연결 상태만 확인
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{settings.MINIO_ENDPOINT}/minio/health/live")
            if response.status_code == 200:
                return StorageStatus(
                    name="MinIO",
                    used_bytes=0,
                    total_bytes=0,
                    used_percent=0,
                    status="healthy",
                )
    except:
        pass

    return None


async def get_system_status(db: Session) -> SystemStatusResponse:
    """전체 시스템 상태 조회"""
    # 모든 서비스 상태를 병렬로 확인
    services = await asyncio.gather(
        check_database(db),
        check_redis(),
        check_minio(),
        check_qdrant(),
        check_vlm(db),
    )

    workers = await get_worker_status()
    gpu = await get_gpu_status()
    storage = await get_storage_status()

    # 전체 상태 결정
    unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
    offline_workers = sum(1 for w in workers if w.status == "offline")

    if unhealthy_count == 0 and offline_workers == 0:
        overall_status = "healthy"
    elif unhealthy_count >= 2 or offline_workers >= 2:
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return SystemStatusResponse(
        timestamp=datetime.utcnow(),
        overall_status=overall_status,
        services=list(services),
        workers=workers,
        gpu=gpu,
        storage=storage,
    )
