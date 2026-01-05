from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class VLMModelInfo(BaseModel):
    """VLM 모델 정보"""
    id: str
    name: str
    description: Optional[str] = None


class SettingsBase(BaseModel):
    """설정 기본 스키마"""
    # 타임존
    timezone: str = Field(default="Asia/Seoul", description="IANA 타임존")

    # OCR 설정
    ocr_default_mode: str = Field(default="auto", description="기본 OCR 모드 (auto, fast, accurate, precision)")
    ocr_precision_threshold: int = Field(default=60, ge=0, le=100, description="자동 모드에서 precision으로 전환하는 임계값 (0-100)")
    ocr_high_res_dpi: int = Field(default=300, ge=72, le=600, description="고해상도 스캔 DPI")
    ocr_language: str = Field(default="kor+eng", description="OCR 언어 설정")
    ocr_preserve_layout: int = Field(default=1, ge=0, le=1, description="레이아웃 보존 여부 (0: 비활성화, 1: 활성화)")

    # VLM 설정
    vlm_endpoint_url: str = Field(default="", description="VLM API 엔드포인트 URL")
    vlm_model_name: str = Field(default="", description="사용할 VLM 모델명")
    vlm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    vlm_max_tokens: int = Field(default=4096, ge=1, le=32768)
    vlm_top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    vlm_timeout: int = Field(default=120, ge=10, le=600)
    vlm_extra_params: Dict[str, Any] = Field(default_factory=dict)

    # 문서 보관 정책 설정
    retention_enabled: int = Field(default=0, ge=0, le=1, description="자동 정리 활성화 (0: 비활성화, 1: 활성화)")
    retention_days: int = Field(default=90, ge=1, le=3650, description="보관 기간 (일)")
    retention_min_documents: int = Field(default=100, ge=0, le=10000, description="최소 보관 문서 수")
    retention_delete_files: int = Field(default=1, ge=0, le=1, description="스토리지 파일도 삭제 (0: DB만, 1: 파일도)")
    retention_auto_run_hour: int = Field(default=3, ge=0, le=23, description="자동 실행 시간 (0-23시)")

    # 로그 설정
    log_level: str = Field(default="info", description="로그 레벨 (debug, info, warning, error)")
    log_retention_days: int = Field(default=30, ge=1, le=365, description="로그 보존 기간 (일)")

    # 알림 설정
    notification_enabled: int = Field(default=0, ge=0, le=1, description="알림 활성화 (0: 비활성화, 1: 활성화)")
    notification_email: str = Field(default="", description="알림 이메일 (쉼표로 구분)")
    notification_webhook_url: str = Field(default="", description="웹훅 URL")
    notification_on_ocr_complete: int = Field(default=0, ge=0, le=1, description="OCR 완료 시 알림")
    notification_on_ocr_error: int = Field(default=1, ge=0, le=1, description="OCR 오류 시 알림")
    notification_on_storage_warning: int = Field(default=1, ge=0, le=1, description="스토리지 경고 시 알림")
    notification_storage_threshold: int = Field(default=80, ge=0, le=100, description="스토리지 경고 임계값 (%)")


class SettingsUpdate(BaseModel):
    """설정 업데이트용 스키마 (부분 업데이트 지원)"""
    timezone: Optional[str] = None
    # OCR 설정
    ocr_default_mode: Optional[str] = None
    ocr_precision_threshold: Optional[int] = Field(None, ge=0, le=100)
    ocr_high_res_dpi: Optional[int] = Field(None, ge=72, le=600)
    ocr_language: Optional[str] = None
    ocr_preserve_layout: Optional[int] = Field(None, ge=0, le=1)
    # VLM 설정
    vlm_endpoint_url: Optional[str] = None
    vlm_model_name: Optional[str] = None
    vlm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    vlm_max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    vlm_top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    vlm_timeout: Optional[int] = Field(None, ge=10, le=600)
    vlm_extra_params: Optional[Dict[str, Any]] = None
    # 문서 보관 정책 설정
    retention_enabled: Optional[int] = Field(None, ge=0, le=1)
    retention_days: Optional[int] = Field(None, ge=1, le=3650)
    retention_min_documents: Optional[int] = Field(None, ge=0, le=10000)
    retention_delete_files: Optional[int] = Field(None, ge=0, le=1)
    retention_auto_run_hour: Optional[int] = Field(None, ge=0, le=23)
    # 로그 설정
    log_level: Optional[str] = None
    log_retention_days: Optional[int] = Field(None, ge=1, le=365)
    # 알림 설정
    notification_enabled: Optional[int] = Field(None, ge=0, le=1)
    notification_email: Optional[str] = None
    notification_webhook_url: Optional[str] = None
    notification_on_ocr_complete: Optional[int] = Field(None, ge=0, le=1)
    notification_on_ocr_error: Optional[int] = Field(None, ge=0, le=1)
    notification_on_storage_warning: Optional[int] = Field(None, ge=0, le=1)
    notification_storage_threshold: Optional[int] = Field(None, ge=0, le=100)


class SettingsResponse(SettingsBase):
    """설정 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimezoneInfo(BaseModel):
    """타임존 정보"""
    value: str
    label: str
    offset: Optional[str] = None


class TimezoneListResponse(BaseModel):
    """타임존 목록 응답"""
    common: List[str]  # 자주 사용되는 타임존
    all: List[str]     # 전체 타임존


class VLMConnectionTestRequest(BaseModel):
    """VLM 연결 테스트 요청"""
    endpoint_url: str
    model_name: Optional[str] = None


class VLMConnectionTestResponse(BaseModel):
    """VLM 연결 테스트 응답"""
    success: bool
    message: str
    available_models: List[VLMModelInfo] = []
    latency_ms: Optional[float] = None
