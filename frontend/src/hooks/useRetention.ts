'use client';

import { useState, useCallback } from 'react';

const getApiBase = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export interface DocumentPreview {
  id: number;
  filename: string;
  created_at: string;
  file_size?: number;
}

export interface CleanupPreview {
  count: number;
  total_size_bytes: number;
  oldest_date?: string;
  newest_date?: string;
  retention_days: number;
  min_documents: number;
  delete_files: boolean;
  documents: DocumentPreview[];
}

export interface CleanupResult {
  deleted_count: number;
  deleted_size_bytes: number;
  remaining_documents: number;
  errors: Array<{
    document_id: number;
    filename: string;
    error: string;
  }>;
}

export function useRetention() {
  const [preview, setPreview] = useState<CleanupPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreview = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBase()}/api/v1/retention/preview`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setPreview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '정리 미리보기 조회 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  const executeCleanup = useCallback(async (): Promise<CleanupResult | null> => {
    setExecuting(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBase()}/api/v1/retention/execute`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      // 정리 후 미리보기 갱신
      await fetchPreview();

      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : '문서 정리 실패');
      return null;
    } finally {
      setExecuting(false);
    }
  }, [fetchPreview]);

  // 바이트를 사람이 읽기 쉬운 형식으로 변환
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return {
    preview,
    loading,
    executing,
    error,
    fetchPreview,
    executeCleanup,
    formatBytes,
  };
}
