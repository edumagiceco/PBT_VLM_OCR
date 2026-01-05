"""
시스템 상태 모니터링 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.system import SystemStatusResponse
from app.services import system_service


router = APIRouter()


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: Session = Depends(get_db)):
    """
    시스템 전체 상태 조회

    - 데이터베이스, Redis, MinIO, Qdrant, VLM 서버 상태
    - 워커 큐 상태
    - GPU 상태 (가용시)
    - 스토리지 상태
    """
    return await system_service.get_system_status(db)
