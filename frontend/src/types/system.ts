export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency_ms?: number;
  message?: string;
  details?: Record<string, unknown>;
}

export interface WorkerQueueStatus {
  name: string;
  queue_name: string;
  active_tasks: number;
  reserved_tasks: number;
  workers: number;
  status: 'active' | 'idle' | 'offline';
}

export interface GPUStatus {
  index: number;
  name: string;
  memory_used_mb: number;
  memory_total_mb: number;
  memory_percent: number;
  gpu_utilization: number;
  temperature?: number;
  status: 'available' | 'busy' | 'unavailable';
}

export interface StorageStatus {
  name: string;
  used_bytes: number;
  total_bytes: number;
  used_percent: number;
  status: 'healthy' | 'warning' | 'critical';
}

export interface SystemStatusResponse {
  timestamp: string;
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  services: ServiceStatus[];
  workers: WorkerQueueStatus[];
  gpu?: GPUStatus[];
  storage?: StorageStatus;
}
