FROM python:3.11-slim

WORKDIR /app

# System dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Celery worker
CMD ["celery", "-A", "app.core.celery_app", "worker", "-Q", "general_ocr", "-c", "4", "--loglevel=info"]
