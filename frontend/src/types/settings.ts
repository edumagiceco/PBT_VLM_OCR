export interface VLMModelInfo {
  id: string;
  name: string;
  description?: string;
}

export interface Settings {
  id: number;
  timezone: string;
  // OCR 설정
  ocr_default_mode: string;
  ocr_precision_threshold: number;
  ocr_high_res_dpi: number;
  ocr_language: string;
  ocr_preserve_layout: number;
  // VLM 설정
  vlm_endpoint_url: string;
  vlm_model_name: string;
  vlm_temperature: number;
  vlm_max_tokens: number;
  vlm_top_p: number;
  vlm_timeout: number;
  vlm_extra_params: Record<string, unknown>;
  // 문서 보관 정책 설정
  retention_enabled: number;
  retention_days: number;
  retention_min_documents: number;
  retention_delete_files: number;
  retention_auto_run_hour: number;
  // 로그 설정
  log_level: string;
  log_retention_days: number;
  // 알림 설정
  notification_enabled: number;
  notification_email: string;
  notification_webhook_url: string;
  notification_on_ocr_complete: number;
  notification_on_ocr_error: number;
  notification_on_storage_warning: number;
  notification_storage_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface SettingsUpdate {
  timezone?: string;
  // OCR 설정
  ocr_default_mode?: string;
  ocr_precision_threshold?: number;
  ocr_high_res_dpi?: number;
  ocr_language?: string;
  ocr_preserve_layout?: number;
  // VLM 설정
  vlm_endpoint_url?: string;
  vlm_model_name?: string;
  vlm_temperature?: number;
  vlm_max_tokens?: number;
  vlm_top_p?: number;
  vlm_timeout?: number;
  vlm_extra_params?: Record<string, unknown>;
  // 문서 보관 정책 설정
  retention_enabled?: number;
  retention_days?: number;
  retention_min_documents?: number;
  retention_delete_files?: number;
  retention_auto_run_hour?: number;
  // 로그 설정
  log_level?: string;
  log_retention_days?: number;
  // 알림 설정
  notification_enabled?: number;
  notification_email?: string;
  notification_webhook_url?: string;
  notification_on_ocr_complete?: number;
  notification_on_ocr_error?: number;
  notification_on_storage_warning?: number;
  notification_storage_threshold?: number;
}

export interface TimezoneListResponse {
  common: string[];
  all: string[];
}

export interface VLMConnectionTestRequest {
  endpoint_url: string;
  model_name?: string;
}

export interface VLMConnectionTestResponse {
  success: boolean;
  message: string;
  available_models: VLMModelInfo[];
  latency_ms?: number;
}
