'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  FileText,
  ArrowLeft,
  AlertCircle,
} from 'lucide-react';
import { documentApi } from '@/lib/api';
import type { ProcessingQueueResponse, ProcessingQueueItem } from '@/types/document';

const STATUS_CONFIG = {
  pending: {
    label: '대기 중',
    color: 'bg-yellow-100 text-yellow-800',
    icon: Clock,
  },
  processing: {
    label: '처리 중',
    color: 'bg-blue-100 text-blue-800',
    icon: Loader2,
  },
  completed: {
    label: '완료',
    color: 'bg-green-100 text-green-800',
    icon: CheckCircle,
  },
  failed: {
    label: '실패',
    color: 'bg-red-100 text-red-800',
    icon: XCircle,
  },
  review: {
    label: '검수 필요',
    color: 'bg-purple-100 text-purple-800',
    icon: AlertCircle,
  },
};

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function getTimeDiff(start: string, end: string | null): string {
  if (!end) return '-';
  const diff = new Date(end).getTime() - new Date(start).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}초`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}분 ${remainingSeconds}초`;
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const isProcessing = status === 'processing';

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}>
      <Icon className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
      {config.label}
    </span>
  );
}

function QueueItem({ item, onClick }: { item: ProcessingQueueItem; onClick: () => void }) {
  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={onClick}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
          <div className="min-w-0">
            <p className="font-medium text-gray-900 truncate">{item.title}</p>
            <p className="text-sm text-gray-500 truncate">{item.original_filename}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={item.status} />
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {item.ocr_mode === 'precision' ? '프리미엄(GPU)' : item.ocr_mode === 'accurate' ? '고급(CPU)' : item.ocr_mode === 'fast' ? '기본(CPU)' : '자동'}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {item.page_count > 0 ? `${item.page_count}p` : '-'}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {formatFileSize(item.file_size)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {formatTime(item.created_at)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {getTimeDiff(item.created_at, item.processed_at)}
      </td>
      <td className="px-4 py-3">
        {item.error_message && (
          <span className="text-xs text-red-600 truncate block max-w-[150px]" title={item.error_message}>
            {item.error_message}
          </span>
        )}
      </td>
    </tr>
  );
}

export default function ProcessingQueuePage() {
  const router = useRouter();
  const [queue, setQueue] = useState<ProcessingQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchQueue = useCallback(async () => {
    try {
      const data = await documentApi.getProcessingQueue();
      setQueue(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchQueue, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchQueue]);

  const handleRefresh = () => {
    setLoading(true);
    fetchQueue();
  };

  if (loading && !queue) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">OCR 처리 현황</h1>
            <p className="text-sm text-gray-500">
              실시간 문서 처리 상태를 확인하세요
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300"
            />
            자동 새로고침 (3초)
          </label>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      {queue && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">전체</p>
            <p className="text-2xl font-bold text-gray-900">{queue.total}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg shadow p-4">
            <p className="text-sm text-yellow-600">대기 중</p>
            <p className="text-2xl font-bold text-yellow-700">{queue.pending}</p>
          </div>
          <div className="bg-blue-50 rounded-lg shadow p-4">
            <p className="text-sm text-blue-600">처리 중</p>
            <p className="text-2xl font-bold text-blue-700">{queue.processing}</p>
          </div>
          <div className="bg-green-50 rounded-lg shadow p-4">
            <p className="text-sm text-green-600">완료</p>
            <p className="text-2xl font-bold text-green-700">{queue.completed}</p>
          </div>
          <div className="bg-red-50 rounded-lg shadow p-4">
            <p className="text-sm text-red-600">실패</p>
            <p className="text-2xl font-bold text-red-700">{queue.failed}</p>
          </div>
        </div>
      )}

      {/* Queue Table */}
      {queue && queue.items.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  문서
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  OCR 모드
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  페이지
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  파일 크기
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  요청 시간
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  처리 시간
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  오류
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {queue.items.map((item) => (
                <QueueItem
                  key={item.id}
                  item={item}
                  onClick={() => router.push(`/documents/${item.id}`)}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FileText className="w-12 h-12 mx-auto text-gray-300" />
          <p className="mt-2 text-gray-500">처리 중인 문서가 없습니다.</p>
        </div>
      )}
    </div>
  );
}
