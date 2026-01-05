'use client';

import { useState, useCallback } from 'react';
import type {
  StorageStatsResponse,
  OrphanedFilesResponse,
  CleanupResponse,
} from '@/types/storage';

const getApiBase = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export function useStorage() {
  const [stats, setStats] = useState<StorageStatsResponse | null>(null);
  const [orphanedFiles, setOrphanedFiles] = useState<OrphanedFilesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBase()}/api/v1/storage/stats`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '스토리지 정보 조회 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchOrphanedFiles = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBase()}/api/v1/storage/orphaned`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setOrphanedFiles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '고아 파일 조회 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  const cleanupOrphanedFiles = useCallback(async (): Promise<CleanupResponse | null> => {
    setCleaning(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBase()}/api/v1/storage/cleanup`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      // 정리 후 통계 및 고아 파일 목록 갱신
      await fetchStats();
      await fetchOrphanedFiles();

      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : '스토리지 정리 실패');
      return null;
    } finally {
      setCleaning(false);
    }
  }, [fetchStats, fetchOrphanedFiles]);

  // 바이트를 사람이 읽기 쉬운 형식으로 변환
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return {
    stats,
    orphanedFiles,
    loading,
    cleaning,
    error,
    fetchStats,
    fetchOrphanedFiles,
    cleanupOrphanedFiles,
    formatBytes,
  };
}
