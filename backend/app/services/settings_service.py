"""
설정 관리 서비스

타임존, VLM 설정 등 전역 설정 관리
"""
import time
from typing import Optional, List

import httpx
import pytz
from sqlalchemy.orm import Session

from app.models.settings import Settings
from app.schemas.settings import (
    SettingsUpdate,
    TimezoneListResponse,
    VLMConnectionTestRequest,
    VLMConnectionTestResponse,
    VLMModelInfo,
)


# 자주 사용되는 타임존 목록
COMMON_TIMEZONES = [
    "Asia/Seoul",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Hong_Kong",
    "UTC",
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Australia/Sydney",
]


async def get_settings(db: Session) -> Settings:
    """
    설정 조회 (없으면 기본값으로 생성)
    싱글톤 패턴: id=1 레코드만 사용
    """
    settings = db.query(Settings).filter(Settings.id == 1).first()
    if not settings:
        settings = Settings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


async def update_settings(db: Session, update_data: SettingsUpdate) -> Settings:
    """
    설정 업데이트 (부분 업데이트 지원)
    """
    settings = await get_settings(db)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings


def get_timezone_list() -> TimezoneListResponse:
    """
    사용 가능한 타임존 목록 조회
    """
    return TimezoneListResponse(
        common=COMMON_TIMEZONES,
        all=sorted(pytz.all_timezones),
    )


def validate_timezone(timezone: str) -> bool:
    """타임존 유효성 검사"""
    return timezone in pytz.all_timezones


async def test_vlm_connection(
    request: VLMConnectionTestRequest
) -> VLMConnectionTestResponse:
    """
    VLM 엔드포인트 연결 테스트

    OpenAI 호환 API 형식 (vLLM, Ollama 등)을 가정
    """
    try:
        start_time = time.time()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # /v1/models 엔드포인트로 모델 목록 조회 시도
            base_url = request.endpoint_url.rstrip('/')
            models_url = f"{base_url}/v1/models"

            response = await client.get(models_url)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models: List[VLMModelInfo] = []

                # OpenAI 형식의 응답 파싱
                if "data" in data:
                    for model in data["data"]:
                        models.append(VLMModelInfo(
                            id=model.get("id", ""),
                            name=model.get("id", ""),
                            description=model.get("owned_by", ""),
                        ))

                return VLMConnectionTestResponse(
                    success=True,
                    message="연결 성공",
                    available_models=models,
                    latency_ms=round(latency_ms, 2),
                )
            else:
                return VLMConnectionTestResponse(
                    success=False,
                    message=f"서버 응답 오류: HTTP {response.status_code}",
                    available_models=[],
                )

    except httpx.TimeoutException:
        return VLMConnectionTestResponse(
            success=False,
            message="연결 시간 초과 (10초)",
            available_models=[],
        )
    except httpx.ConnectError:
        return VLMConnectionTestResponse(
            success=False,
            message="서버에 연결할 수 없습니다",
            available_models=[],
        )
    except Exception as e:
        return VLMConnectionTestResponse(
            success=False,
            message=f"연결 실패: {str(e)}",
            available_models=[],
        )
