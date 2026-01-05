"""
시스템 상태 모니터링 스키마
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    """개별 서비스 상태"""
    name: str
    status: str  # "healthy", "unhealthy", "unknown"
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: Optional[dict] = None


class WorkerQueueStatus(BaseModel):
    """워커 큐 상태"""
    name: str
    queue_name: str
    active_tasks: int
    reserved_tasks: int
    workers: int
    status: str  # "active", "idle", "offline"


class GPUStatus(BaseModel):
    """GPU 상태"""
    index: int
    name: str
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    gpu_utilization: float
    temperature: Optional[float] = None
    status: str  # "available", "busy", "unavailable"


class StorageStatus(BaseModel):
    """스토리지 상태"""
    name: str
    used_bytes: int
    total_bytes: int
    used_percent: float
    status: str  # "healthy", "warning", "critical"


class SystemStatusResponse(BaseModel):
    """시스템 전체 상태 응답"""
    timestamp: datetime
    overall_status: str  # "healthy", "degraded", "unhealthy"
    services: List[ServiceStatus]
    workers: List[WorkerQueueStatus]
    gpu: Optional[List[GPUStatus]] = None
    storage: Optional[StorageStatus] = None
