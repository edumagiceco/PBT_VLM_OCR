export interface StorageCategoryStats {
  size_bytes: number;
  count: number;
}

export interface StorageStatsResponse {
  bucket_name: string;
  total_size_bytes: number;
  total_objects: number;
  categories: {
    documents: StorageCategoryStats;
    pages: StorageCategoryStats;
    thumbnails: StorageCategoryStats;
    other: StorageCategoryStats;
  };
  error?: string;
}

export interface OrphanedFile {
  object_name: string;
  size: number;
  last_modified?: string;
}

export interface OrphanedFilesResponse {
  count: number;
  total_size_bytes: number;
  files: OrphanedFile[];
}

export interface CleanupResponse {
  deleted_count: number;
  deleted_size_bytes: number;
  errors: Array<{
    object_name?: string;
    error: string;
  }>;
}
