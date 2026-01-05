'use client';

import { useState, useCallback } from 'react';
import type { SystemStatusResponse } from '@/types/system';

const getApiBase = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBase()}/api/v1/system/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '시스템 상태 조회 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    status,
    loading,
    error,
    fetchStatus,
  };
}
