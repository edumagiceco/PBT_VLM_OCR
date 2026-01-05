#!/usr/bin/env python3
"""
MinIO 버킷 초기화 스크립트
"""
from minio import Minio
from minio.error import S3Error
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "pbt-ocr-documents")


def init_minio():
    """MinIO 버킷 생성"""
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    # 버킷 생성
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        print(f"Bucket '{MINIO_BUCKET}' created successfully!")
    else:
        print(f"Bucket '{MINIO_BUCKET}' already exists.")


if __name__ == "__main__":
    try:
        init_minio()
    except S3Error as e:
        print(f"Error: {e}")
