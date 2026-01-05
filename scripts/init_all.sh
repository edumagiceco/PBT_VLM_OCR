#!/bin/bash
# 전체 초기화 스크립트
# 데이터베이스, MinIO, 마이그레이션을 한 번에 설정

set -e

echo "=========================================="
echo "PBT VLM OCR Suite - 초기화 시작"
echo "=========================================="

# 서비스 대기
echo "서비스 시작 대기 중..."
sleep 5

# PostgreSQL 연결 대기
echo "PostgreSQL 연결 대기 중..."
until pg_isready -h postgres -p 5432 -U postgres 2>/dev/null; do
    echo "PostgreSQL 연결 대기..."
    sleep 2
done
echo "PostgreSQL 연결 완료!"

# pg_trgm 확장 설치 (Full-text search용)
echo "PostgreSQL 확장 설치 중..."
PGPASSWORD=postgres psql -h postgres -U postgres -d pbt_ocr -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" 2>/dev/null || true

# Alembic 마이그레이션 실행
echo "데이터베이스 마이그레이션 실행 중..."
cd /app
alembic upgrade head

# MinIO 버킷 초기화
echo "MinIO 버킷 초기화 중..."
python /app/scripts/init_minio.py

echo "=========================================="
echo "초기화 완료!"
echo "=========================================="
