# GPU 기반 정밀 OCR Worker
# VLM 구현 참고: https://github.com/datalab-to/chandra

FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-kor \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# GPU Celery worker
CMD ["celery", "-A", "app.core.celery_app", "worker", "-Q", "precision_ocr", "-c", "1", "--loglevel=info"]
