from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "pbt_ocr_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="fast_ocr",
    # 큐 라우팅은 document_service에서 동적으로 처리
    # fast_ocr: Tesseract 기반 빠른 처리
    # accurate_ocr: PaddleOCR 딥러닝 기반
    # precision_ocr: Chandra VLM 기반
    task_routes={
        "cleanup_document_files": {"queue": "fast_ocr"},
        "generate_embeddings": {"queue": "fast_ocr"},
    },
)
