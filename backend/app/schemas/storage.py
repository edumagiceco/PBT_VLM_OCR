"""
스토리지 관리 스키마
"""
from typing import Optional, List, Dict
from pydantic import BaseModel


class StorageCategoryStats(BaseModel):
    """스토리지 카테고리별 통계"""
    size_bytes: int
    count: int


class StorageStatsResponse(BaseModel):
    """스토리지 통계 응답"""
    bucket_name: str
    total_size_bytes: int
    total_objects: int
    categories: Dict[str, StorageCategoryStats]
    error: Optional[str] = None


class OrphanedFile(BaseModel):
    """고아 파일 정보"""
    object_name: str
    size: int
    last_modified: Optional[str] = None


class OrphanedFilesResponse(BaseModel):
    """고아 파일 목록 응답"""
    count: int
    total_size_bytes: int
    files: List[OrphanedFile]


class CleanupError(BaseModel):
    """정리 오류"""
    object_name: Optional[str] = None
    error: str


class CleanupResponse(BaseModel):
    """정리 결과 응답"""
    deleted_count: int
    deleted_size_bytes: int
    errors: List[CleanupError]
