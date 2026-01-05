#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트

사용법:
    python scripts/migrate.py upgrade      # 최신 버전으로 업그레이드
    python scripts/migrate.py downgrade    # 한 단계 롤백
    python scripts/migrate.py current      # 현재 버전 확인
    python scripts/migrate.py history      # 마이그레이션 히스토리
    python scripts/migrate.py generate "메시지"  # 새 마이그레이션 생성
"""
import os
import sys
import subprocess

# 프로젝트 루트로 이동
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_APP_DIR = os.path.join(BACKEND_DIR, "backend")


def run_alembic(args: list):
    """Alembic 명령 실행"""
    os.chdir(BACKEND_APP_DIR)
    cmd = ["alembic"] + args
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)


def upgrade(revision: str = "head"):
    """마이그레이션 업그레이드"""
    run_alembic(["upgrade", revision])


def downgrade(revision: str = "-1"):
    """마이그레이션 롤백"""
    run_alembic(["downgrade", revision])


def current():
    """현재 마이그레이션 버전 확인"""
    run_alembic(["current"])


def history():
    """마이그레이션 히스토리"""
    run_alembic(["history", "--verbose"])


def generate(message: str):
    """새 마이그레이션 자동 생성"""
    run_alembic(["revision", "--autogenerate", "-m", message])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        upgrade(revision)
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        downgrade(revision)
    elif command == "current":
        current()
    elif command == "history":
        history()
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Error: Message required for generate command")
            sys.exit(1)
        generate(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
