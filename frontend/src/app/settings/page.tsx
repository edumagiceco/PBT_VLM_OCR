'use client';

import { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Globe,
  Cpu,
  Save,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  TestTube,
  FileText,
  Activity,
  Database,
  HardDrive,
  Server,
  Zap,
  Trash2,
  AlertTriangle,
  FolderOpen,
  Image,
  File,
  Clock,
  Calendar,
  Archive,
  Bell,
  Mail,
  Webhook,
  ScrollText,
} from 'lucide-react';
import { useSettings } from '@/hooks/useSettings';
import { useSystemStatus } from '@/hooks/useSystemStatus';
import { useStorage } from '@/hooks/useStorage';
import { useRetention } from '@/hooks/useRetention';
import type { VLMModelInfo } from '@/types/settings';

export default function SettingsPage() {
  const {
    settings,
    timezones,
    loading,
    saving,
    error,
    fetchSettings,
    updateSettings,
    testVLMConnection,
  } = useSettings();

  const {
    status: systemStatus,
    loading: statusLoading,
    fetchStatus,
  } = useSystemStatus();

  const {
    stats: storageStats,
    orphanedFiles,
    loading: storageLoading,
    cleaning,
    fetchStats,
    fetchOrphanedFiles,
    cleanupOrphanedFiles,
    formatBytes,
  } = useStorage();

  const {
    preview: retentionPreview,
    loading: retentionLoading,
    executing: retentionExecuting,
    fetchPreview: fetchRetentionPreview,
    executeCleanup: executeRetentionCleanup,
    formatBytes: formatRetentionBytes,
  } = useRetention();

  // 보관 정책 정리 확인 모달
  const [showRetentionCleanupConfirm, setShowRetentionCleanupConfirm] = useState(false);
  const [retentionCleanupResult, setRetentionCleanupResult] = useState<{
    deleted_count: number;
    deleted_size_bytes: number;
  } | null>(null);

  // 정리 확인 모달
  const [showCleanupConfirm, setShowCleanupConfirm] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<{
    deleted_count: number;
    deleted_size_bytes: number;
  } | null>(null);

  // 폼 상태
  const [formData, setFormData] = useState({
    timezone: 'Asia/Seoul',
    // OCR 설정
    ocr_default_mode: 'auto',
    ocr_precision_threshold: 60,
    ocr_high_res_dpi: 300,
    ocr_language: 'kor+eng',
    ocr_preserve_layout: 1,
    // VLM 설정
    vlm_endpoint_url: '',
    vlm_model_name: '',
    vlm_temperature: 0,
    vlm_max_tokens: 4096,
    vlm_top_p: 1.0,
    vlm_timeout: 120,
    // 문서 보관 정책 설정
    retention_enabled: 0,
    retention_days: 90,
    retention_min_documents: 100,
    retention_delete_files: 1,
    retention_auto_run_hour: 3,
    // 로그 설정
    log_level: 'info',
    log_retention_days: 30,
    // 알림 설정
    notification_enabled: 0,
    notification_email: '',
    notification_webhook_url: '',
    notification_on_ocr_complete: 0,
    notification_on_ocr_error: 1,
    notification_on_storage_warning: 1,
    notification_storage_threshold: 80,
  });

  // VLM 테스트 상태
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    latency_ms?: number;
  } | null>(null);
  const [testing, setTesting] = useState(false);
  const [availableModels, setAvailableModels] = useState<VLMModelInfo[]>([]);

  // 저장 성공 메시지
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchSettings();
    fetchStatus();
    fetchStats();
    fetchOrphanedFiles();
    fetchRetentionPreview();
  }, [fetchSettings, fetchStatus, fetchStats, fetchOrphanedFiles, fetchRetentionPreview]);

  useEffect(() => {
    if (settings) {
      setFormData({
        timezone: settings.timezone,
        // OCR 설정
        ocr_default_mode: settings.ocr_default_mode || 'auto',
        ocr_precision_threshold: settings.ocr_precision_threshold ?? 60,
        ocr_high_res_dpi: settings.ocr_high_res_dpi ?? 300,
        ocr_language: settings.ocr_language || 'kor+eng',
        ocr_preserve_layout: settings.ocr_preserve_layout ?? 1,
        // VLM 설정
        vlm_endpoint_url: settings.vlm_endpoint_url,
        vlm_model_name: settings.vlm_model_name,
        vlm_temperature: settings.vlm_temperature,
        vlm_max_tokens: settings.vlm_max_tokens,
        vlm_top_p: settings.vlm_top_p,
        vlm_timeout: settings.vlm_timeout,
        // 문서 보관 정책 설정
        retention_enabled: settings.retention_enabled ?? 0,
        retention_days: settings.retention_days ?? 90,
        retention_min_documents: settings.retention_min_documents ?? 100,
        retention_delete_files: settings.retention_delete_files ?? 1,
        retention_auto_run_hour: settings.retention_auto_run_hour ?? 3,
        // 로그 설정
        log_level: settings.log_level || 'info',
        log_retention_days: settings.log_retention_days ?? 30,
        // 알림 설정
        notification_enabled: settings.notification_enabled ?? 0,
        notification_email: settings.notification_email || '',
        notification_webhook_url: settings.notification_webhook_url || '',
        notification_on_ocr_complete: settings.notification_on_ocr_complete ?? 0,
        notification_on_ocr_error: settings.notification_on_ocr_error ?? 1,
        notification_on_storage_warning: settings.notification_on_storage_warning ?? 1,
        notification_storage_threshold: settings.notification_storage_threshold ?? 80,
      });
    }
  }, [settings]);

  const handleTestConnection = async () => {
    if (!formData.vlm_endpoint_url) return;

    setTesting(true);
    setTestResult(null);

    try {
      const result = await testVLMConnection({
        endpoint_url: formData.vlm_endpoint_url,
      });
      setTestResult({
        success: result.success,
        message: result.message,
        latency_ms: result.latency_ms,
      });
      if (result.success && result.available_models.length > 0) {
        setAvailableModels(result.available_models);
      }
    } catch {
      setTestResult({
        success: false,
        message: '테스트 중 오류가 발생했습니다',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    try {
      await updateSettings(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error handled in hook
    }
  };

  const handleReset = () => {
    if (settings) {
      setFormData({
        timezone: settings.timezone,
        // OCR 설정
        ocr_default_mode: settings.ocr_default_mode || 'auto',
        ocr_precision_threshold: settings.ocr_precision_threshold ?? 60,
        ocr_high_res_dpi: settings.ocr_high_res_dpi ?? 300,
        ocr_language: settings.ocr_language || 'kor+eng',
        ocr_preserve_layout: settings.ocr_preserve_layout ?? 1,
        // VLM 설정
        vlm_endpoint_url: settings.vlm_endpoint_url,
        vlm_model_name: settings.vlm_model_name,
        vlm_temperature: settings.vlm_temperature,
        vlm_max_tokens: settings.vlm_max_tokens,
        vlm_top_p: settings.vlm_top_p,
        vlm_timeout: settings.vlm_timeout,
        // 문서 보관 정책 설정
        retention_enabled: settings.retention_enabled ?? 0,
        retention_days: settings.retention_days ?? 90,
        retention_min_documents: settings.retention_min_documents ?? 100,
        retention_delete_files: settings.retention_delete_files ?? 1,
        retention_auto_run_hour: settings.retention_auto_run_hour ?? 3,
        // 로그 설정
        log_level: settings.log_level || 'info',
        log_retention_days: settings.log_retention_days ?? 30,
        // 알림 설정
        notification_enabled: settings.notification_enabled ?? 0,
        notification_email: settings.notification_email || '',
        notification_webhook_url: settings.notification_webhook_url || '',
        notification_on_ocr_complete: settings.notification_on_ocr_complete ?? 0,
        notification_on_ocr_error: settings.notification_on_ocr_error ?? 1,
        notification_on_storage_warning: settings.notification_on_storage_warning ?? 1,
        notification_storage_threshold: settings.notification_storage_threshold ?? 80,
      });
    }
    setTestResult(null);
    setAvailableModels([]);
  };

  const handleRetentionCleanup = async () => {
    const result = await executeRetentionCleanup();
    if (result) {
      setRetentionCleanupResult({
        deleted_count: result.deleted_count,
        deleted_size_bytes: result.deleted_size_bytes,
      });
    }
    setShowRetentionCleanupConfirm(false);
  };

  const handleCleanup = async () => {
    const result = await cleanupOrphanedFiles();
    if (result) {
      setCleanupResult({
        deleted_count: result.deleted_count,
        deleted_size_bytes: result.deleted_size_bytes,
      });
    }
    setShowCleanupConfirm(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon className="w-6 h-6 text-gray-600" />
        <h1 className="text-2xl font-bold text-gray-900">환경 설정</h1>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {saveSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          설정이 저장되었습니다.
        </div>
      )}

      <div className="space-y-6">
        {/* 시스템 상태 모니터링 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-semibold text-gray-900">시스템 상태</h2>
            </div>
            <div className="flex items-center gap-2">
              {systemStatus && (
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    systemStatus.overall_status === 'healthy'
                      ? 'bg-green-100 text-green-700'
                      : systemStatus.overall_status === 'degraded'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {systemStatus.overall_status === 'healthy'
                    ? '정상'
                    : systemStatus.overall_status === 'degraded'
                    ? '일부 문제'
                    : '오류'}
                </span>
              )}
              <button
                onClick={fetchStatus}
                disabled={statusLoading}
                className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50"
                title="새로고침"
              >
                <RefreshCw className={`w-4 h-4 ${statusLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {statusLoading && !systemStatus ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : systemStatus ? (
            <div className="space-y-4">
              {/* 서비스 상태 */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                  <Server className="w-4 h-4" />
                  서비스
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
                  {systemStatus.services.map((service) => (
                    <div
                      key={service.name}
                      className={`p-3 rounded-lg border ${
                        service.status === 'healthy'
                          ? 'bg-green-50 border-green-200'
                          : service.status === 'unhealthy'
                          ? 'bg-red-50 border-red-200'
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            service.status === 'healthy'
                              ? 'bg-green-500'
                              : service.status === 'unhealthy'
                              ? 'bg-red-500'
                              : 'bg-gray-400'
                          }`}
                        />
                        <span className="text-sm font-medium text-gray-900">
                          {service.name}
                        </span>
                      </div>
                      {service.latency_ms && (
                        <p className="text-xs text-gray-500 mt-1">
                          {service.latency_ms}ms
                        </p>
                      )}
                      {service.status === 'unhealthy' && service.message && (
                        <p className="text-xs text-red-600 mt-1 truncate">
                          {service.message}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 워커 상태 */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  OCR 워커
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {systemStatus.workers.map((worker) => (
                    <div
                      key={worker.name}
                      className={`p-3 rounded-lg border ${
                        worker.status === 'active'
                          ? 'bg-blue-50 border-blue-200'
                          : worker.status === 'idle'
                          ? 'bg-gray-50 border-gray-200'
                          : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full ${
                              worker.status === 'active'
                                ? 'bg-blue-500 animate-pulse'
                                : worker.status === 'idle'
                                ? 'bg-gray-400'
                                : 'bg-red-500'
                            }`}
                          />
                          <span className="text-sm font-medium text-gray-900">
                            {worker.name}
                          </span>
                        </div>
                        <span
                          className={`text-xs px-2 py-0.5 rounded ${
                            worker.status === 'active'
                              ? 'bg-blue-100 text-blue-700'
                              : worker.status === 'idle'
                              ? 'bg-gray-100 text-gray-600'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {worker.status === 'active'
                            ? '처리중'
                            : worker.status === 'idle'
                            ? '대기'
                            : '오프라인'}
                        </span>
                      </div>
                      {worker.active_tasks > 0 && (
                        <p className="text-xs text-gray-500 mt-1">
                          대기 작업: {worker.active_tasks}개
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* GPU 상태 (있는 경우) */}
              {systemStatus.gpu && systemStatus.gpu.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    <HardDrive className="w-4 h-4" />
                    GPU
                  </h3>
                  <div className="grid grid-cols-1 gap-2">
                    {systemStatus.gpu.map((gpu) => (
                      <div
                        key={gpu.index}
                        className={`p-3 rounded-lg border ${
                          gpu.status === 'available'
                            ? 'bg-green-50 border-green-200'
                            : gpu.status === 'busy'
                            ? 'bg-yellow-50 border-yellow-200'
                            : 'bg-red-50 border-red-200'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full ${
                              gpu.status === 'available'
                                ? 'bg-green-500'
                                : gpu.status === 'busy'
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                          />
                          <span className="text-sm font-medium text-gray-900">
                            {gpu.name}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded ${
                              gpu.status === 'available'
                                ? 'bg-green-100 text-green-700'
                                : gpu.status === 'busy'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {gpu.status === 'available'
                              ? '사용 가능'
                              : gpu.status === 'busy'
                              ? '사용중'
                              : '사용 불가'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 마지막 업데이트 시간 */}
              <p className="text-xs text-gray-400 text-right">
                마지막 업데이트: {new Date(systemStatus.timestamp).toLocaleString('ko-KR')}
              </p>
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-4">
              시스템 상태를 불러올 수 없습니다.
            </p>
          )}
        </section>

        {/* 스토리지 관리 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-orange-600" />
              <h2 className="text-lg font-semibold text-gray-900">스토리지 관리</h2>
            </div>
            <button
              onClick={() => {
                fetchStats();
                fetchOrphanedFiles();
              }}
              disabled={storageLoading}
              className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50"
              title="새로고침"
            >
              <RefreshCw className={`w-4 h-4 ${storageLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {storageLoading && !storageStats ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : storageStats ? (
            <div className="space-y-4">
              {/* 전체 사용량 */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">전체 사용량</span>
                  <span className="text-lg font-bold text-gray-900">
                    {formatBytes(storageStats.total_size_bytes)}
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  총 {storageStats.total_objects.toLocaleString()}개 파일
                </p>
              </div>

              {/* 카테고리별 사용량 */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">카테고리별 사용량</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <div className="flex items-center gap-2 mb-1">
                      <File className="w-4 h-4 text-blue-600" />
                      <span className="text-xs font-medium text-blue-700">문서</span>
                    </div>
                    <p className="text-sm font-bold text-gray-900">
                      {formatBytes(storageStats.categories.documents.size_bytes)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {storageStats.categories.documents.count}개
                    </p>
                  </div>

                  <div className="p-3 bg-green-50 rounded-lg border border-green-100">
                    <div className="flex items-center gap-2 mb-1">
                      <Image className="w-4 h-4 text-green-600" />
                      <span className="text-xs font-medium text-green-700">페이지</span>
                    </div>
                    <p className="text-sm font-bold text-gray-900">
                      {formatBytes(storageStats.categories.pages.size_bytes)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {storageStats.categories.pages.count}개
                    </p>
                  </div>

                  <div className="p-3 bg-purple-50 rounded-lg border border-purple-100">
                    <div className="flex items-center gap-2 mb-1">
                      <FolderOpen className="w-4 h-4 text-purple-600" />
                      <span className="text-xs font-medium text-purple-700">썸네일</span>
                    </div>
                    <p className="text-sm font-bold text-gray-900">
                      {formatBytes(storageStats.categories.thumbnails.size_bytes)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {storageStats.categories.thumbnails.count}개
                    </p>
                  </div>

                  <div className="p-3 bg-gray-100 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-2 mb-1">
                      <HardDrive className="w-4 h-4 text-gray-600" />
                      <span className="text-xs font-medium text-gray-700">기타</span>
                    </div>
                    <p className="text-sm font-bold text-gray-900">
                      {formatBytes(storageStats.categories.other.size_bytes)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {storageStats.categories.other.count}개
                    </p>
                  </div>
                </div>
              </div>

              {/* 고아 파일 정리 */}
              <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-yellow-600" />
                      <span className="text-sm font-medium text-yellow-800">
                        고아 파일 (정리 가능)
                      </span>
                    </div>
                    {orphanedFiles ? (
                      <p className="text-xs text-yellow-700">
                        {orphanedFiles.count}개 파일, {formatBytes(orphanedFiles.total_size_bytes)}
                      </p>
                    ) : (
                      <p className="text-xs text-yellow-700">조회 중...</p>
                    )}
                  </div>
                  <button
                    onClick={() => setShowCleanupConfirm(true)}
                    disabled={cleaning || !orphanedFiles || orphanedFiles.count === 0}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {cleaning ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                    정리
                  </button>
                </div>
              </div>

              {/* 정리 결과 메시지 */}
              {cleanupResult && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-sm">
                    {cleanupResult.deleted_count}개 파일 ({formatBytes(cleanupResult.deleted_size_bytes)}) 삭제 완료
                  </span>
                  <button
                    onClick={() => setCleanupResult(null)}
                    className="ml-auto text-green-600 hover:text-green-800"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-4">
              스토리지 정보를 불러올 수 없습니다.
            </p>
          )}
        </section>

        {/* 정리 확인 모달 */}
        {showCleanupConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md mx-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-yellow-100 rounded-full">
                  <AlertTriangle className="w-6 h-6 text-yellow-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">고아 파일 정리</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                DB에 등록되지 않은 {orphanedFiles?.count || 0}개의 파일
                ({formatBytes(orphanedFiles?.total_size_bytes || 0)})을 삭제합니다.
                이 작업은 되돌릴 수 없습니다.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowCleanupConfirm(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  취소
                </button>
                <button
                  onClick={handleCleanup}
                  disabled={cleaning}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {cleaning ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  삭제 실행
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 문서 보관 정책 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Archive className="w-5 h-5 text-teal-600" />
              <h2 className="text-lg font-semibold text-gray-900">문서 보관 정책</h2>
            </div>
            <button
              onClick={fetchRetentionPreview}
              disabled={retentionLoading}
              className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50"
              title="새로고침"
            >
              <RefreshCw className={`w-4 h-4 ${retentionLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-4">
            {/* 자동 정리 활성화 */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.retention_enabled === 1}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      retention_enabled: e.target.checked ? 1 : 0,
                    }))
                  }
                  className="w-5 h-5 text-teal-600 border-gray-300 rounded focus:ring-teal-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">
                    자동 문서 정리 활성화
                  </span>
                  <p className="text-xs text-gray-500">
                    보관 기간이 지난 문서를 자동으로 정리합니다.
                  </p>
                </div>
              </label>
            </div>

            {/* 보관 기간 설정 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  보관 기간
                </label>
                <select
                  value={formData.retention_days}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      retention_days: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                >
                  <option value="30">30일</option>
                  <option value="60">60일</option>
                  <option value="90">90일</option>
                  <option value="180">180일 (6개월)</option>
                  <option value="365">365일 (1년)</option>
                  <option value="730">730일 (2년)</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  이 기간보다 오래된 문서가 정리 대상입니다.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <File className="w-4 h-4 inline mr-1" />
                  최소 보관 문서 수
                </label>
                <input
                  type="number"
                  value={formData.retention_min_documents}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      retention_min_documents: parseInt(e.target.value) || 0,
                    }))
                  }
                  min="0"
                  max="10000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  이 수 이하로는 삭제하지 않습니다.
                </p>
              </div>
            </div>

            {/* 추가 옵션 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Clock className="w-4 h-4 inline mr-1" />
                  자동 실행 시간
                </label>
                <select
                  value={formData.retention_auto_run_hour}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      retention_auto_run_hour: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>
                      {i.toString().padStart(2, '0')}:00
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  자동 정리가 실행되는 시간입니다.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <HardDrive className="w-4 h-4 inline mr-1" />
                  스토리지 파일 삭제
                </label>
                <select
                  value={formData.retention_delete_files}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      retention_delete_files: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                >
                  <option value="1">DB + 스토리지 파일 모두 삭제</option>
                  <option value="0">DB 기록만 삭제 (파일 유지)</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  문서 삭제 시 스토리지 파일도 삭제할지 선택합니다.
                </p>
              </div>
            </div>

            {/* 정리 대상 미리보기 */}
            <div className="p-4 border border-teal-200 bg-teal-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Trash2 className="w-4 h-4 text-teal-600" />
                    <span className="text-sm font-medium text-teal-800">
                      정리 대상 문서
                    </span>
                  </div>
                  {retentionLoading ? (
                    <p className="text-xs text-teal-700">조회 중...</p>
                  ) : retentionPreview ? (
                    <p className="text-xs text-teal-700">
                      {retentionPreview.count}개 문서,{' '}
                      {formatRetentionBytes(retentionPreview.total_size_bytes)}
                    </p>
                  ) : (
                    <p className="text-xs text-teal-700">정보 없음</p>
                  )}
                </div>
                <button
                  onClick={() => setShowRetentionCleanupConfirm(true)}
                  disabled={retentionExecuting || !retentionPreview || retentionPreview.count === 0}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {retentionExecuting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  지금 정리
                </button>
              </div>
            </div>

            {/* 정리 결과 메시지 */}
            {retentionCleanupResult && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">
                  {retentionCleanupResult.deleted_count}개 문서 (
                  {formatRetentionBytes(retentionCleanupResult.deleted_size_bytes)}) 삭제 완료
                </span>
                <button
                  onClick={() => setRetentionCleanupResult(null)}
                  className="ml-auto text-green-600 hover:text-green-800"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </section>

        {/* 보관 정책 정리 확인 모달 */}
        {showRetentionCleanupConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md mx-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-teal-100 rounded-full">
                  <Archive className="w-6 h-6 text-teal-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">문서 정리 실행</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                {retentionPreview?.retention_days}일 이상 된{' '}
                {retentionPreview?.count || 0}개의 문서 (
                {formatRetentionBytes(retentionPreview?.total_size_bytes || 0)})를 삭제합니다.
                {formData.retention_delete_files === 1 &&
                  ' 스토리지 파일도 함께 삭제됩니다.'}
                <br />
                <strong>이 작업은 되돌릴 수 없습니다.</strong>
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowRetentionCleanupConfirm(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  취소
                </button>
                <button
                  onClick={handleRetentionCleanup}
                  disabled={retentionExecuting}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {retentionExecuting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  삭제 실행
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 로그 설정 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <ScrollText className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-gray-900">로그 설정</h2>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  로그 레벨
                </label>
                <select
                  value={formData.log_level}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      log_level: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="debug">Debug - 모든 로그</option>
                  <option value="info">Info - 정보 이상</option>
                  <option value="warning">Warning - 경고 이상</option>
                  <option value="error">Error - 오류만</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  시스템 로그 기록 수준을 설정합니다.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  로그 보존 기간
                </label>
                <select
                  value={formData.log_retention_days}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      log_retention_days: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="7">7일</option>
                  <option value="14">14일</option>
                  <option value="30">30일</option>
                  <option value="60">60일</option>
                  <option value="90">90일</option>
                  <option value="180">180일</option>
                  <option value="365">365일</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  이 기간이 지난 로그는 자동으로 삭제됩니다.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 알림 설정 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bell className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-semibold text-gray-900">알림 설정</h2>
          </div>

          <div className="space-y-4">
            {/* 알림 활성화 */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.notification_enabled === 1}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      notification_enabled: e.target.checked ? 1 : 0,
                    }))
                  }
                  className="w-5 h-5 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">
                    알림 기능 활성화
                  </span>
                  <p className="text-xs text-gray-500">
                    이메일 또는 웹훅으로 시스템 알림을 받습니다.
                  </p>
                </div>
              </label>
            </div>

            {/* 알림 수신 설정 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Mail className="w-4 h-4 inline mr-1" />
                  알림 이메일
                </label>
                <input
                  type="text"
                  value={formData.notification_email}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      notification_email: e.target.value,
                    }))
                  }
                  placeholder="admin@example.com, team@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  여러 이메일은 쉼표로 구분합니다.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Webhook className="w-4 h-4 inline mr-1" />
                  웹훅 URL
                </label>
                <input
                  type="text"
                  value={formData.notification_webhook_url}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      notification_webhook_url: e.target.value,
                    }))
                  }
                  placeholder="https://hooks.slack.com/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Slack, Teams 등의 웹훅 URL을 입력합니다.
                </p>
              </div>
            </div>

            {/* 알림 이벤트 설정 */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">알림 받을 이벤트</h3>
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.notification_on_ocr_complete === 1}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        notification_on_ocr_complete: e.target.checked ? 1 : 0,
                      }))
                    }
                    className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                  />
                  <div>
                    <span className="text-sm text-gray-900">OCR 처리 완료</span>
                    <p className="text-xs text-gray-500">문서 OCR 처리가 완료되면 알림</p>
                  </div>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.notification_on_ocr_error === 1}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        notification_on_ocr_error: e.target.checked ? 1 : 0,
                      }))
                    }
                    className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                  />
                  <div>
                    <span className="text-sm text-gray-900">OCR 처리 오류</span>
                    <p className="text-xs text-gray-500">OCR 처리 중 오류가 발생하면 알림</p>
                  </div>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.notification_on_storage_warning === 1}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        notification_on_storage_warning: e.target.checked ? 1 : 0,
                      }))
                    }
                    className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                  />
                  <div>
                    <span className="text-sm text-gray-900">스토리지 경고</span>
                    <p className="text-xs text-gray-500">스토리지 사용량이 임계값을 초과하면 알림</p>
                  </div>
                </label>
              </div>
            </div>

            {/* 스토리지 경고 임계값 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                스토리지 경고 임계값: {formData.notification_storage_threshold}%
              </label>
              <input
                type="range"
                value={formData.notification_storage_threshold}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    notification_storage_threshold: parseInt(e.target.value),
                  }))
                }
                min="50"
                max="95"
                step="5"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>50%</span>
                <span>70%</span>
                <span>95%</span>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                스토리지 사용량이 이 값을 초과하면 경고 알림을 보냅니다.
              </p>
            </div>
          </div>
        </section>

        {/* 타임존 설정 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">타임존 설정</h2>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              시간대
            </label>
            <select
              value={formData.timezone}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, timezone: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {timezones && (
                <>
                  <optgroup label="자주 사용되는 타임존">
                    {timezones.common.map((tz) => (
                      <option key={`common-${tz}`} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="전체 타임존">
                    {timezones.all.map((tz) => (
                      <option key={`all-${tz}`} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </optgroup>
                </>
              )}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              UI에 표시되는 모든 시간에 적용됩니다.
            </p>
          </div>
        </section>

        {/* OCR 설정 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-green-600" />
            <h2 className="text-lg font-semibold text-gray-900">OCR 설정</h2>
          </div>

          <div className="space-y-4">
            {/* 기본 OCR 모드 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                기본 OCR 모드
              </label>
              <select
                value={formData.ocr_default_mode}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    ocr_default_mode: e.target.value,
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="auto">자동 (문서 특성에 따라 선택)</option>
                <option value="fast">기본 (Fast) - Tesseract, 빠른 처리</option>
                <option value="accurate">고급 (Accurate) - PaddleOCR, CPU 기반</option>
                <option value="precision">프리미엄 (Precision) - VLM, GPU 기반</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">
                문서 업로드 시 기본으로 선택되는 OCR 모드입니다.
              </p>
            </div>

            {/* 정밀도 임계값 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                자동 모드 정밀도 임계값: {formData.ocr_precision_threshold}%
              </label>
              <input
                type="range"
                value={formData.ocr_precision_threshold}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    ocr_precision_threshold: parseInt(e.target.value),
                  }))
                }
                min="0"
                max="100"
                step="5"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0% (항상 Fast)</span>
                <span>50%</span>
                <span>100% (항상 Precision)</span>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                자동 모드에서 Fast OCR 결과의 신뢰도가 이 값 이하일 때 Precision 모드로 전환합니다.
              </p>
            </div>

            {/* 스캔 해상도 및 언어 설정 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  스캔 해상도 (DPI)
                </label>
                <select
                  value={formData.ocr_high_res_dpi}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      ocr_high_res_dpi: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="150">150 DPI (빠른 처리)</option>
                  <option value="200">200 DPI (일반)</option>
                  <option value="300">300 DPI (고품질, 권장)</option>
                  <option value="400">400 DPI (고해상도)</option>
                  <option value="600">600 DPI (최고 품질)</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  높을수록 정확도 향상, 처리 시간 증가
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OCR 언어
                </label>
                <select
                  value={formData.ocr_language}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      ocr_language: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="kor+eng">한국어 + 영어</option>
                  <option value="kor">한국어만</option>
                  <option value="eng">영어만</option>
                  <option value="jpn+eng">일본어 + 영어</option>
                  <option value="chi_sim+eng">중국어(간체) + 영어</option>
                  <option value="chi_tra+eng">중국어(번체) + 영어</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Fast/Accurate 모드에 적용됩니다
                </p>
              </div>
            </div>

            {/* 레이아웃 보존 */}
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.ocr_preserve_layout === 1}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      ocr_preserve_layout: e.target.checked ? 1 : 0,
                    }))
                  }
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  레이아웃 보존
                </span>
              </label>
              <p className="mt-1 text-sm text-gray-500 ml-6">
                활성화 시 문서의 원본 레이아웃(표, 단락 구조 등)을 유지합니다.
              </p>
            </div>
          </div>
        </section>

        {/* VLM 설정 섹션 */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              VLM (Vision Language Model) 설정
            </h2>
          </div>

          <div className="space-y-4">
            {/* 엔드포인트 URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                엔드포인트 URL
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={formData.vlm_endpoint_url}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_endpoint_url: e.target.value,
                    }))
                  }
                  placeholder="http://localhost:8080"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={handleTestConnection}
                  disabled={testing || !formData.vlm_endpoint_url}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4" />
                  )}
                  연결 테스트
                </button>
              </div>

              {/* 테스트 결과 */}
              {testResult && (
                <div
                  className={`mt-2 p-3 rounded-lg text-sm ${
                    testResult.success
                      ? 'bg-green-50 text-green-700'
                      : 'bg-red-50 text-red-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {testResult.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    {testResult.message}
                    {testResult.latency_ms && (
                      <span className="text-xs opacity-75">
                        ({testResult.latency_ms}ms)
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* 모델 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                모델명
              </label>
              {availableModels.length > 0 ? (
                <select
                  value={formData.vlm_model_name}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_model_name: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">모델을 선택하세요</option>
                  {availableModels.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={formData.vlm_model_name}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_model_name: e.target.value,
                    }))
                  }
                  placeholder="모델명 입력 또는 연결 테스트 후 선택"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              )}
              <p className="mt-1 text-sm text-gray-500">
                연결 테스트 후 사용 가능한 모델 목록이 표시됩니다.
              </p>
            </div>

            {/* 파라미터 설정 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  value={formData.vlm_temperature}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_temperature: parseFloat(e.target.value) || 0,
                    }))
                  }
                  min="0"
                  max="2"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  0 = 결정적, 높을수록 무작위
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={formData.vlm_max_tokens}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_max_tokens: parseInt(e.target.value) || 4096,
                    }))
                  }
                  min="1"
                  max="32768"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">최대 출력 토큰 수</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Top P
                </label>
                <input
                  type="number"
                  value={formData.vlm_top_p}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_top_p: parseFloat(e.target.value) || 1.0,
                    }))
                  }
                  min="0"
                  max="1"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">Nucleus sampling</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timeout (초)
                </label>
                <input
                  type="number"
                  value={formData.vlm_timeout}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vlm_timeout: parseInt(e.target.value) || 120,
                    }))
                  }
                  min="10"
                  max="600"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">요청 시간 제한</p>
              </div>
            </div>
          </div>
        </section>

        {/* 저장 버튼 */}
        <div className="flex justify-end gap-3">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            초기화
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            저장
          </button>
        </div>
      </div>
    </div>
  );
}
