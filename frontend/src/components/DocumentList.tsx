'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, Download, Trash2, RefreshCw, Eye } from 'lucide-react';
import { useDocuments } from '@/hooks/useDocuments';
import { documentApi } from '@/lib/api';
import type { Document, DocumentStatus } from '@/types/document';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  review: 'bg-purple-100 text-purple-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  PROCESSING: 'bg-blue-100 text-blue-800',
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  REVIEW: 'bg-purple-100 text-purple-800',
};

const statusLabels: Record<string, string> = {
  pending: '대기 중',
  processing: '처리 중',
  completed: '완료',
  failed: '실패',
  review: '검수 필요',
  PENDING: '대기 중',
  PROCESSING: '처리 중',
  COMPLETED: '완료',
  FAILED: '실패',
  REVIEW: '검수 필요',
};

export default function DocumentList() {
  const router = useRouter();
  const { documents, loading, error, fetchDocuments, deleteDocument } = useDocuments();
  const [search, setSearch] = useState('');
  const [openDropdownId, setOpenDropdownId] = useState<number | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 외부 클릭시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdownId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDocuments({ search });
  };

  const handleDelete = async (id: number) => {
    if (confirm('정말 삭제하시겠습니까?')) {
      await deleteDocument(id);
    }
  };

  const handleDownload = (doc: Document, format: 'md' | 'json' | 'html') => {
    window.open(documentApi.getDownloadUrl(doc.id, format), '_blank');
    setOpenDropdownId(null);
  };

  const toggleDropdown = (docId: number) => {
    setOpenDropdownId(prev => prev === docId ? null : docId);
  };

  if (loading && !documents) {
    return (
      <div className="text-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
        <p className="mt-2 text-gray-500">로딩 중...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">문서 목록</h2>
        <button
          onClick={() => fetchDocuments()}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <RefreshCw className="w-4 h-4" />
          새로고침
        </button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="문서 제목으로 검색..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            검색
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Document Table */}
      {documents && documents.items.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  문서
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  OCR 모드
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  페이지
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  생성일
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {documents.items.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <FileText className="w-5 h-5 text-gray-400 mr-3" />
                      <div>
                        <div className="font-medium text-gray-900">
                          {doc.title}
                        </div>
                        <div className="text-sm text-gray-500">
                          {doc.department || '-'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm">
                      {doc.ocr_mode === 'precision' ? '프리미엄(GPU)' : doc.ocr_mode === 'accurate' ? '고급(CPU)' : doc.ocr_mode === 'fast' ? '기본(CPU)' : '자동'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        statusColors[doc.status]
                      }`}
                    >
                      {statusLabels[doc.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {doc.page_count}p
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(doc.created_at).toLocaleDateString('ko-KR')}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => router.push(`/documents/${doc.id}`)}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="상세 보기"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {doc.status.toLowerCase() === 'completed' && (
                        <div className="relative" ref={openDropdownId === doc.id ? dropdownRef : null}>
                          <button
                            onClick={() => toggleDropdown(doc.id)}
                            className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded"
                            title="다운로드"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          {openDropdownId === doc.id && (
                            <div className="absolute right-0 top-full mt-1 bg-white border rounded-lg shadow-lg z-10 min-w-[120px]">
                              <button
                                onClick={() => handleDownload(doc, 'md')}
                                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100 rounded-t-lg"
                              >
                                Markdown
                              </button>
                              <button
                                onClick={() => handleDownload(doc, 'json')}
                                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
                              >
                                JSON
                              </button>
                              <button
                                onClick={() => handleDownload(doc, 'html')}
                                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100 rounded-b-lg"
                              >
                                HTML
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        title="삭제"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {documents.total > documents.page_size && (
            <div className="px-6 py-3 border-t border-gray-200 flex justify-between items-center">
              <span className="text-sm text-gray-500">
                총 {documents.total}개 중 {documents.items.length}개 표시
              </span>
              <div className="flex gap-2">
                {/* TODO: Pagination controls */}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg">
          <FileText className="w-12 h-12 mx-auto text-gray-300" />
          <p className="mt-2 text-gray-500">등록된 문서가 없습니다.</p>
        </div>
      )}
    </div>
  );
}
