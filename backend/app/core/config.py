from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PBT OCR Solution"
    API_V1_STR: str = "/api/v1"

    # CORS - 모든 오리진 허용 (개발 환경) 또는 환경변수로 설정
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pbt_ocr"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_EXTERNAL_ENDPOINT: str = ""  # External endpoint for browser-accessible URLs
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "pbt-ocr-documents"
    MINIO_SECURE: bool = False

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # OCR Settings
    OCR_PRECISION_THRESHOLD: int = 60
    OCR_DEFAULT_MODE: str = "auto"
    OCR_HIGH_RES_DPI: int = 300

    # VLM Settings (for GPU-based Precision OCR)
    VLM_API_BASE: str = "http://localhost:8080/v1"
    VLM_MODEL_NAME: str = "qwen3-vl"
    VLM_MAX_TOKENS: int = 8192
    VLM_TIMEOUT: int = 120  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
