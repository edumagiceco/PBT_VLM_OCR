'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Download, RefreshCw, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { documentApi } from '@/lib/api';
import { useDocument } from '@/hooks/useDocuments';
import type { Document } from '@/types/document';
import PageViewer from '@/components/review/PageViewer';
import BlockEditor from '@/components/review/BlockEditor';
import DocumentInfo from '@/components/review/DocumentInfo';

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = Number(params.id);

  const {
    document,
    loading,
    updating,
    error,
    fetchDocument,
    updateDocument,
    updateBlock,
    reprocessDocument,
  } = useDocument(documentId);

  const [selectedPageNo, setSelectedPageNo] = useState(1);
  const [selectedBlockId, setSelectedBlockId] = useState<number | null>(null);
  const [showInfo, setShowInfo] = useState(false);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  const downloadMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  // 외부 클릭시 다운로드 메뉴 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (downloadMenuRef.current && !downloadMenuRef.current.contains(event.target as Node)) {
        setShowDownloadMenu(false);
      }
    };
    window.document.addEventListener('mousedown', handleClickOutside);
    return () => window.document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownload = (format: 'md' | 'json' | 'html') => {
    window.open(documentApi.getDownloadUrl(documentId, format), '_blank');
    setShowDownloadMenu(false);
  };

  const handleReprocess = async () => {
    if (!confirm('OCR을 다시 처리하시겠습니까?')) return;
    try {
      await reprocessDocument();
      router.push('/');
    } catch (err) {
      alert('재처리 요청 실패');
    }
  };

  const handleBlockUpdate = async (blockId: number, text: string) => {
    try {
      await updateBlock(blockId, { text });
      setSelectedBlockId(null);
    } catch (err) {
      alert('블록 수정 실패');
    }
  };

  const handleDocumentUpdate = async (data: Partial<Document>) => {
    try {
      await updateDocument(data);
    } catch (err) {
      alert('문서 정보 수정 실패');
      throw err;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-400" />
        <p className="mt-4 text-red-600">{error || '문서를 찾을 수 없습니다.'}</p>
        <button
          onClick={() => router.back()}
          className="mt-4 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
        >
          돌아가기
        </button>
      </div>
    );
  }

  const currentPage = document.pages.find(p => p.page_no === selectedPageNo);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.back()}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-lg font-bold">{document.title}</h1>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span>{document.page_count}페이지</span>
                  <span>•</span>
                  <span>
                    {document.ocr_mode === 'precision' ? '프리미엄(GPU)' : document.ocr_mode === 'accurate' ? '고급(CPU)' : document.ocr_mode === 'fast' ? '기본(CPU)' : '자동'}
                  </span>
                  <span>•</span>
                  <StatusBadge status={document.status} />
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowInfo(!showInfo)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                  showInfo ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Info className="w-4 h-4" />
                정보
              </button>
              <button
                onClick={handleReprocess}
                disabled={updating}
                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${updating ? 'animate-spin' : ''}`} />
                재처리
              </button>
              <div className="relative" ref={downloadMenuRef}>
                <button
                  onClick={() => setShowDownloadMenu(prev => !prev)}
                  className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Download className="w-4 h-4" />
                  다운로드
                </button>
                {showDownloadMenu && (
                  <div className="absolute right-0 top-full mt-1 bg-white border rounded-lg shadow-lg z-20 min-w-[120px]">
                    <button
                      onClick={() => handleDownload('md')}
                      className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100 rounded-t-lg"
                    >
                      Markdown
                    </button>
                    <button
                      onClick={() => handleDownload('json')}
                      className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
                    >
                      JSON
                    </button>
                    <button
                      onClick={() => handleDownload('html')}
                      className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100 rounded-b-lg"
                    >
                      HTML
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Document Info Slide Panel */}
      {showInfo && (
        <div className="fixed inset-0 z-20" onClick={() => setShowInfo(false)}>
          <div className="absolute inset-0 bg-black/20" />
          <div
            className="absolute right-0 top-0 h-full w-96 bg-white shadow-xl overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
              <h2 className="font-bold">문서 상세 정보</h2>
              <button
                onClick={() => setShowInfo(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                ✕
              </button>
            </div>
            <DocumentInfo
              document={document}
              onUpdate={handleDocumentUpdate}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-4">
          {/* Left Sidebar - Page Thumbnails */}
          <div className="col-span-1">
            <div className="bg-white rounded-lg shadow p-1 sticky top-20">
              <div className="space-y-1 max-h-[calc(100vh-150px)] overflow-y-auto">
                {document.pages
                  .sort((a, b) => a.page_no - b.page_no)
                  .map(page => (
                    <button
                      key={page.id}
                      onClick={() => setSelectedPageNo(page.page_no)}
                      className={`w-full p-1 rounded text-center transition-colors text-sm font-medium ${
                        selectedPageNo === page.page_no
                          ? 'bg-blue-500 text-white'
                          : 'hover:bg-gray-100 text-gray-600'
                      }`}
                    >
                      {page.page_no}
                    </button>
                  ))}
              </div>
            </div>
          </div>

          {/* Center - Page Viewer */}
          <div className="col-span-7">
            {currentPage ? (
              <PageViewer
                documentId={documentId}
                page={currentPage}
                selectedBlockId={selectedBlockId}
                onBlockSelect={setSelectedBlockId}
              />
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                페이지를 선택하세요
              </div>
            )}
          </div>

          {/* Right Sidebar - Block Editor */}
          <div className="col-span-4 max-h-[calc(100vh-150px)] overflow-y-auto">
            <div className="bg-white rounded-lg shadow sticky top-20">
              {currentPage ? (
                <BlockEditor
                  page={currentPage}
                  selectedBlockId={selectedBlockId}
                  onBlockSelect={setSelectedBlockId}
                  onBlockUpdate={handleBlockUpdate}
                />
              ) : (
                <div className="p-8 text-center text-gray-500">
                  페이지를 선택하세요
                </div>
              )}
            </div>
          </div>
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
