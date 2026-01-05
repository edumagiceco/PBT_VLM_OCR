.PHONY: help dev prod down logs init clean migrate vlm-start vlm-stop vlm-logs vlm-test

help:
	@echo "PBT OCR Solution - Development Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make dev           Start development environment (no GPU)"
	@echo "  make prod          Start production environment (with GPU)"
	@echo "  make down          Stop all containers"
	@echo "  make logs          View logs"
	@echo "  make init          Initialize database and storage"
	@echo "  make clean         Remove all containers and volumes"
	@echo ""
	@echo "VLM (GPU OCR):"
	@echo "  make vlm-start     Start VLM server (GPU required)"
	@echo "  make vlm-stop      Stop VLM server"
	@echo "  make vlm-logs      View VLM server logs"
	@echo "  make vlm-test      Test VLM server"
	@echo "  make vlm-build     Build VLM Docker image"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       Run database migrations"
	@echo "  make migrate-gen   Generate new migration (MSG=message)"
	@echo "  make migrate-down  Rollback one migration"
	@echo "  make migrate-hist  Show migration history"
	@echo ""

# Development environment (no GPU)
dev:
	docker-compose -f docker-compose.dev.yml up -d
	@echo ""
	@echo "Services started:"
	@echo "  - Frontend:  http://localhost:3000"
	@echo "  - Backend:   http://localhost:8000"
	@echo "  - API Docs:  http://localhost:8000/docs"
	@echo "  - MinIO:     http://localhost:9001"
	@echo "  - Qdrant:    http://localhost:6333/dashboard"
	@echo ""

# Production environment (with GPU)
prod:
	docker-compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  - Frontend:  http://localhost:3000"
	@echo "  - Backend:   http://localhost:8000"
	@echo "  - MinIO:     http://localhost:9001"
	@echo "  - Qdrant:    http://localhost:6333/dashboard"
	@echo ""

# Stop all containers
down:
	docker-compose -f docker-compose.dev.yml down
	docker-compose down

# View logs
logs:
	docker-compose -f docker-compose.dev.yml logs -f

logs-backend:
	docker-compose -f docker-compose.dev.yml logs -f backend

logs-worker:
	docker-compose -f docker-compose.dev.yml logs -f worker-general-ocr

# Initialize database and storage (full)
init:
	@echo "Waiting for services to start..."
	sleep 5
	@echo "Creating pg_trgm extension..."
	docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d pbt_ocr -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" || true
	@echo "Running database migrations..."
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
	@echo "Initializing MinIO bucket..."
	docker-compose -f docker-compose.dev.yml exec backend python /app/scripts/init_minio.py
	@echo ""
	@echo "Initialization complete!"

# Database migrations
migrate:
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

migrate-gen:
	@if [ -z "$(MSG)" ]; then echo "Usage: make migrate-gen MSG='migration message'"; exit 1; fi
	docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	docker-compose -f docker-compose.dev.yml exec backend alembic downgrade -1

migrate-hist:
	docker-compose -f docker-compose.dev.yml exec backend alembic history --verbose

migrate-current:
	docker-compose -f docker-compose.dev.yml exec backend alembic current

# Clean up everything
clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose down -v
	@echo "All containers and volumes removed."

# Build images
build:
	docker-compose -f docker-compose.dev.yml build

# Run tests
test:
	docker-compose -f docker-compose.dev.yml exec backend pytest tests/ -v

# Shell access
shell-backend:
	docker-compose -f docker-compose.dev.yml exec backend bash

shell-db:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d pbt_ocr

# =========================================
# VLM (GPU-based Precision OCR)
# =========================================

# Build VLM Docker image
vlm-build:
	docker-compose build chandra-vllm
	@echo "VLM Docker image built successfully."

# Start VLM server (requires NVIDIA GPU)
vlm-start:
	@echo "Starting VLM server (GPU required)..."
	@echo "This may take several minutes on first run (downloading model)..."
	docker-compose up -d chandra-vllm
	@echo ""
	@echo "VLM server starting..."
	@echo "  - API: http://localhost:8080/v1"
	@echo "  - Health: http://localhost:8080/health"
	@echo ""
	@echo "Check logs: make vlm-logs"
	@echo "Test server: make vlm-test"

# Stop VLM server
vlm-stop:
	docker-compose stop chandra-vllm
	@echo "VLM server stopped."

# View VLM server logs
vlm-logs:
	docker-compose logs -f chandra-vllm

# Test VLM server
vlm-test:
	@echo "Testing VLM server..."
	python3 scripts/test_vlm.py --api-base http://localhost:8080/v1

# Check GPU status
gpu-status:
	nvidia-smi

# Start precision OCR worker
worker-precision:
	docker-compose up -d worker-precision-ocr
	@echo "Precision OCR worker started."

# View precision OCR worker logs
worker-precision-logs:
	docker-compose logs -f worker-precision-ocr
