from fastapi import APIRouter

from app.api.v1 import documents, files, retention, settings, storage, system

router = APIRouter()

router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(files.router, prefix="/files", tags=["files"])
router.include_router(retention.router, prefix="/retention", tags=["retention"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(storage.router, prefix="/storage", tags=["storage"])
router.include_router(system.router, prefix="/system", tags=["system"])
