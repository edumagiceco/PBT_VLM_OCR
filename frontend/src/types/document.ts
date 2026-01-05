export type OCRMode = 'fast' | 'accurate' | 'precision' | 'auto';
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'review';
export type Importance = 'low' | 'medium' | 'high';
export type BlockType = 'text' | 'table' | 'image' | 'header' | 'footer' | 'list';

export interface DocumentBlock {
  id: number;
  page_id: number;
  block_order: number;
  block_type: BlockType;
  bbox: number[] | null;
  text: string | null;
  table_json: Record<string, unknown> | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentPage {
  id: number;
  document_id: number;
  page_no: number;
  image_path: string | null;
  width: number | null;
  height: number | null;
  ocr_json: Record<string, unknown> | null;
  raw_text: string | null;
  layout_score: number | null;
  confidence: number | null;
  blocks: DocumentBlock[];
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  title: string;
  original_filename: string;
  file_path: string;
  file_size: number | null;
  file_type: string | null;
  mime_type: string | null;
  page_count: number;
  department: string | null;
  doc_type: string | null;
  importance: Importance;
  ocr_mode: OCRMode;
  recommended_ocr_mode: OCRMode | null;
  precision_score: number | null;
  status: DocumentStatus;
  error_message: string | null;
  processing_time: number | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
  pages: DocumentPage[];
}

export interface DocumentListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Document[];
}

export interface OCRModeRecommendation {
  recommended_mode: OCRMode;
  precision_score: number;
  reasons: string[];
}

export interface DocumentUploadParams {
  file: File;
  title?: string;
  department?: string;
  doc_type?: string;
  importance?: Importance;
  ocr_mode?: OCRMode;
}

export interface ProcessingQueueItem {
  id: number;
  title: string;
  original_filename: string;
  status: DocumentStatus;
  ocr_mode: OCRMode;
  page_count: number;
  file_size: number | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
  error_message: string | null;
}

export interface ProcessingQueueResponse {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  items: ProcessingQueueItem[];
}
