"""
문서 보관 정책 서비스

오래된 문서 자동 정리 기능 제공
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.settings import Settings
from app.services.storage_service import storage_service


class RetentionService:
    """문서 보관 정책 서비스"""

    def get_retention_settings(self, db: Session) -> Dict:
        """현재 보관 정책 설정 조회"""
        settings = db.query(Settings).filter(Settings.id == 1).first()
        if not settings:
            return {
                "enabled": False,
                "days": 90,
                "min_documents": 100,
                "delete_files": True,
                "auto_run_hour": 3,
            }
        return {
            "enabled": settings.retention_enabled == 1,
            "days": settings.retention_days,
            "min_documents": settings.retention_min_documents,
            "delete_files": settings.retention_delete_files == 1,
            "auto_run_hour": settings.retention_auto_run_hour,
        }

    def get_documents_for_cleanup(
        self,
        db: Session,
        days: int,
        min_documents: int,
    ) -> List[Document]:
        """
        정리 대상 문서 조회

        Args:
            db: 데이터베이스 세션
            days: 보관 기간 (일)
            min_documents: 최소 보관 문서 수

        Returns:
            정리 대상 문서 목록
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 전체 문서 수 조회
        total_count = db.query(func.count(Document.id)).scalar() or 0

        # 최소 보관 문서 수보다 적으면 삭제하지 않음
        if total_count <= min_documents:
            return []

        # 삭제 가능한 최대 문서 수
        max_deletable = total_count - min_documents

        # 오래된 문서 조회 (처리 완료된 것만)
        query = (
            db.query(Document)
            .filter(
                and_(
                    Document.created_at < cutoff_date,
                    Document.status == "completed",
                )
            )
            .order_by(Document.created_at.asc())
            .limit(max_deletable)
        )

        return query.all()

    def preview_cleanup(self, db: Session) -> Dict:
        """
        정리 미리보기 (실제 삭제하지 않음)

        Returns:
            정리 대상 정보
        """
        settings = self.get_retention_settings(db)

        documents = self.get_documents_for_cleanup(
            db,
            settings["days"],
            settings["min_documents"],
        )

        total_size = 0
        for doc in documents:
            if doc.file_size:
                total_size += doc.file_size

        # 가장 오래된 문서와 가장 최근 문서 날짜
        oldest_date = None
        newest_date = None
        if documents:
            oldest_date = documents[0].created_at.isoformat()
            newest_date = documents[-1].created_at.isoformat()

        return {
            "count": len(documents),
            "total_size_bytes": total_size,
            "oldest_date": oldest_date,
            "newest_date": newest_date,
            "retention_days": settings["days"],
            "min_documents": settings["min_documents"],
            "delete_files": settings["delete_files"],
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.original_filename,
                    "created_at": doc.created_at.isoformat(),
                    "file_size": doc.file_size,
                }
                for doc in documents[:20]  # 미리보기는 20개만
            ],
        }

    def execute_cleanup(
        self,
        db: Session,
        delete_files: bool = True,
    ) -> Dict:
        """
        문서 정리 실행

        Args:
            db: 데이터베이스 세션
            delete_files: 스토리지 파일도 삭제 여부

        Returns:
            정리 결과
        """
        settings = self.get_retention_settings(db)

        documents = self.get_documents_for_cleanup(
            db,
            settings["days"],
            settings["min_documents"],
        )

        deleted_count = 0
        deleted_size = 0
        errors = []

        for doc in documents:
            try:
                doc_id = doc.id
                file_size = doc.file_size or 0

                # 스토리지 파일 삭제
                if delete_files:
                    # 원본 문서 파일 삭제
                    if doc.file_path:
                        storage_service.delete_file(doc.file_path)

                    # 페이지 이미지 및 썸네일 삭제
                    storage_service.delete_document_files(doc_id)

                # DB에서 문서 삭제 (CASCADE로 페이지도 삭제됨)
                db.delete(doc)

                deleted_count += 1
                deleted_size += file_size

            except Exception as e:
                errors.append({
                    "document_id": doc.id,
                    "filename": doc.original_filename,
                    "error": str(e),
                })

        # 커밋
        if deleted_count > 0:
            db.commit()

        return {
            "deleted_count": deleted_count,
            "deleted_size_bytes": deleted_size,
            "errors": errors,
            "remaining_documents": db.query(func.count(Document.id)).scalar() or 0,
        }


# 싱글톤 인스턴스
retention_service = RetentionService()
