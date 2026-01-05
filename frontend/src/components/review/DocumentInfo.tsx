'use client';

import { useState } from 'react';
import { FileText, Calendar, Building2, Tag, Cpu, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import type { Document } from '@/types/document';

interface DocumentInfoProps {
  document: Document;
  onUpdate?: (data: Partial<Document>) => Promise<void>;
}

export default function DocumentInfo({ document, onUpdate }: DocumentInfoProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(document.title);
  const [department, setDepartment] = useState(document.department || '');
  const [docType, setDocType] = useState(document.doc_type || '');
  const [importance, setImportance] = useState(document.importance || 'medium');

  const handleSave = async () => {
    if (onUpdate) {
      await onUpdate({
        title,
        department: department || undefined,
        doc_type: docType || undefined,
        importance,
      });
    }
    setIsEditing(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const importanceLabels: Record<string, string> = {
    high: '높음',
    medium: '보통',
    low: '낮음',
  };

  const ocrModeLabels: Record<string, string> = {
    fast: '기본(CPU)',
    accurate: '고급(CPU)',
    precision: '프리미엄(GPU)',
    auto: '자동',
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <h3 className="font-medium">문서 정보</h3>
        {onUpdate && (
          <button
            onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
            className={`px-3 py-1 text-sm rounded ${
              isEditing
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {isEditing ? '저장' : '수정'}
          </button>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Title */}
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <FileText className="w-4 h-4" />
            문서명
          </label>
          {isEditing ? (
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          ) : (
            <p className="font-medium">{document.title}</p>
          )}
        </div>

        {/* Department */}
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Building2 className="w-4 h-4" />
            부서
          </label>
          {isEditing ? (
            <input
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="부서명 입력"
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          ) : (
            <p>{document.department || '-'}</p>
          )}
        </div>

        {/* Document Type */}
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Tag className="w-4 h-4" />
            문서 유형
          </label>
          {isEditing ? (
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">선택하세요</option>
              <option value="contract">계약서</option>
              <option value="invoice">청구서</option>
              <option value="report">보고서</option>
              <option value="letter">서신</option>
              <option value="form">양식</option>
              <option value="other">기타</option>
            </select>
          ) : (
            <p>{document.doc_type || '-'}</p>
          )}
        </div>

        {/* Importance */}
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            중요도
          </label>
          {isEditing ? (
            <select
              value={importance}
              onChange={(e) => setImportance(e.target.value as 'low' | 'medium' | 'high')}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="high">높음</option>
              <option value="medium">보통</option>
              <option value="low">낮음</option>
            </select>
          ) : (
            <span
              className={`inline-flex px-2 py-0.5 text-sm rounded ${
                document.importance === 'high'
                  ? 'bg-red-100 text-red-700'
                  : document.importance === 'low'
                  ? 'bg-gray-100 text-gray-600'
                  : 'bg-yellow-100 text-yellow-700'
              }`}
            >
              {importanceLabels[document.importance || 'medium']}
            </span>
          )}
        </div>

        <hr className="border-gray-200" />

        {/* OCR Mode */}
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Cpu className="w-4 h-4" />
            OCR 모드
          </label>
          <p>{ocrModeLabels[document.ocr_mode] || document.ocr_mode}</p>
        </div>

        {/* Status */}
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            처리 상태
          </label>
          <div className="flex items-center gap-2">
            {getStatusIcon(document.status)}
            <StatusBadge status={document.status} />
          </div>
        </div>

        {/* Processing Time */}
        {document.processing_time && (
          <div>
            <label className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <Clock className="w-4 h-4" />
              처리 시간
            </label>
            <p>{document.processing_time.toFixed(2)}초</p>
          </div>
        )}

        <hr className="border-gray-200" />

        {/* File Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">파일 크기</span>
            <p>{formatFileSize(document.file_size ?? undefined)}</p>
          </div>
          <div>
            <span className="text-gray-500">페이지 수</span>
            <p>{document.page_count}페이지</p>
          </div>
          <div>
            <span className="text-gray-500">파일 형식</span>
            <p className="uppercase">{document.file_type || '-'}</p>
          </div>
          <div>
            <span className="text-gray-500">평균 신뢰도</span>
            <p>
              {document.pages.length > 0
                ? `${(
                    (document.pages.reduce((sum, p) => sum + (p.confidence || 0), 0) /
                      document.pages.length) *
                    100
                  ).toFixed(1)}%`
                : '-'}
            </p>
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* Dates */}
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-400" />
            <span className="text-gray-500">업로드:</span>
            <span>{formatDate(document.created_at)}</span>
          </div>
          {document.processed_at && (
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">처리 완료:</span>
              <span>{formatDate(document.processed_at)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    pending: { color: 'bg-yellow-100 text-yellow-800', label: '대기 중' },
    processing: { color: 'bg-blue-100 text-blue-800', label: '처리 중' },
    completed: { color: 'bg-green-100 text-green-800', label: '완료' },
    failed: { color: 'bg-red-100 text-red-800', label: '실패' },
    review: { color: 'bg-purple-100 text-purple-800', label: '검수 필요' },
  };

  const { color, label } = config[status] || config.pending;

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}
