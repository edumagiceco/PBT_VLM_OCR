#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트

Alembic 마이그레이션을 사용하여 테이블 생성
"""
import os
import sys
import subprocess

# 프로젝트 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_extension():
    """PostgreSQL pg_trgm 확장 설치"""
    try:
        import psycopg2
        from app.core.config import settings

        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.close()
        conn.close()
        print("pg_trgm extension created successfully!")
    except Exception as e:
        print(f"Warning: Could not create pg_trgm extension: {e}")


def run_migrations():
    """Alembic 마이그레이션 실행"""
    print("Running database migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("Database migrations completed successfully!")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"Migration failed: {result.stderr}")
        sys.exit(1)


def init_db():
    """데이터베이스 초기화"""
    print("=" * 50)
    print("Database Initialization")
    print("=" * 50)

    # pg_trgm 확장 설치
    create_extension()

    # Alembic 마이그레이션 실행
    run_migrations()

    print("=" * 50)
    print("Database initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    init_db()
