import { useState, useCallback } from 'react';
import { documentApi } from '@/lib/api';
import type { Document, DocumentListResponse, DocumentUploadParams } from '@/types/document';

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    department?: string;
    status?: string;
    importance?: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await documentApi.list(params);
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (params: DocumentUploadParams) => {
    setLoading(true);
    setError(null);
    try {
      const doc = await documentApi.upload(params);
      return doc;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteDocument = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      await documentApi.delete(id);
      // Refresh the list
      await fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchDocuments]);

  return {
    documents,
    loading,
    error,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
  };
}

export function useDocument(id: number | null) {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  const fetchDocument = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await documentApi.get(id);
      setDocument(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch document');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const updateDocument = useCallback(async (data: Partial<Document>) => {
    if (!id) return;
    setUpdating(true);
    try {
      const updated = await documentApi.update(id, data);
      setDocument(updated);
      return updated;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to update document');
    } finally {
      setUpdating(false);
    }
  }, [id]);

  const updateBlock = useCallback(async (
    blockId: number,
    data: { text?: string; table_json?: Record<string, unknown> }
  ) => {
    if (!id) return;
    setUpdating(true);
    try {
      const updated = await documentApi.updateBlock(id, blockId, data);
      setDocument(updated);
      return updated;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to update block');
    } finally {
      setUpdating(false);
    }
  }, [id]);

  const reprocessDocument = useCallback(async (ocrMode?: string) => {
    if (!id) return;
    setUpdating(true);
    try {
      const updated = await documentApi.reprocess(id, ocrMode);
      setDocument(updated);
      return updated;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to reprocess document');
    } finally {
      setUpdating(false);
    }
  }, [id]);

  const getRecommendation = useCallback(async () => {
    if (!id) return null;
    try {
      return await documentApi.recommendOCRMode(id);
    } catch (err) {
      console.error('Failed to get OCR recommendation:', err);
      return null;
    }
  }, [id]);

  return {
    document,
    loading,
    updating,
    error,
    fetchDocument,
    updateDocument,
    updateBlock,
    reprocessDocument,
    getRecommendation,
    setDocument,
  };
}
