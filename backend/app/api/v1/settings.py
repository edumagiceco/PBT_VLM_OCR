from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.settings import (
    SettingsResponse,
    SettingsUpdate,
    TimezoneListResponse,
    VLMConnectionTestRequest,
    VLMConnectionTestResponse,
)
from app.services import settings_service


router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    현재 설정 조회
    """
    return await settings_service.get_settings(db)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    update_data: SettingsUpdate,
    db: Session = Depends(get_db),
):
    """
    설정 업데이트 (부분 업데이트 지원)
    """
    # 타임존 유효성 검사
    if update_data.timezone is not None:
        if not settings_service.validate_timezone(update_data.timezone):
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 타임존: {update_data.timezone}"
            )

    return await settings_service.update_settings(db, update_data)


@router.get("/timezones", response_model=TimezoneListResponse)
async def get_timezones():
    """
    사용 가능한 타임존 목록 조회
    """
    return settings_service.get_timezone_list()


@router.post("/vlm/test", response_model=VLMConnectionTestResponse)
async def test_vlm_connection(request: VLMConnectionTestRequest):
    """
    VLM 엔드포인트 연결 테스트

    - 엔드포인트에 연결 가능한지 확인
    - 사용 가능한 모델 목록 조회
    - 응답 지연 시간 측정
    """
    return await settings_service.test_vlm_connection(request)
