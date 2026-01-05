'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';
import { useDocuments } from '@/hooks/useDocuments';
import type { OCRMode, Importance } from '@/types/document';

export default function DocumentUpload() {
  const { uploadDocument, loading, error } = useDocuments();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    doc_type: '',
    importance: 'medium' as Importance,
    ocr_mode: 'fast' as OCRMode,  // 기본값: 빠른 OCR
  });
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setFormData((prev) => ({
        ...prev,
        title: acceptedFiles[0].name.replace(/\.[^/.]+$/, ''),
      }));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff'],
    },
    maxFiles: 1,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      await uploadDocument({
        file: selectedFile,
        ...formData,
      });
      setUploadSuccess(true);
      setSelectedFile(null);
      setFormData({
        title: '',
        department: '',
        doc_type: '',
        importance: 'medium',
        ocr_mode: 'fast',
      });
    } catch (err) {
      // Error is handled in the hook
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">문서 업로드</h2>

      {uploadSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          문서가 성공적으로 업로드되었습니다. OCR 처리가 시작됩니다.
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          {selectedFile ? (
            <div className="flex items-center justify-center gap-2">
              <FileText className="w-8 h-8 text-blue-500" />
              <span className="text-lg">{selectedFile.name}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                }}
                className="ml-2 p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          ) : (
            <div>
              <Upload className="w-12 h-12 mx-auto text-gray-400 mb-2" />
              <p className="text-gray-600">
                파일을 드래그하거나 클릭하여 선택하세요
              </p>
              <p className="text-sm text-gray-400 mt-1">
                PDF, PNG, JPG, TIFF 지원
              </p>
            </div>
          )}
        </div>

        {/* Form Fields */}
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              제목
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, title: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              부서
            </label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, department: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              문서 유형
            </label>
            <select
              value={formData.doc_type}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, doc_type: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">선택하세요</option>
              <option value="contract">계약서</option>
              <option value="financial">재무</option>
              <option value="legal">법무</option>
              <option value="research">연구</option>
              <option value="general">일반</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              중요도
            </label>
            <select
              value={formData.importance}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  importance: e.target.value as Importance,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="low">낮음</option>
              <option value="medium">보통</option>
              <option value="high">높음</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              OCR 모드
            </label>
            <select
              value={formData.ocr_mode}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  ocr_mode: e.target.value as OCRMode,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="fast">기본(CPU)</option>
              <option value="accurate">고급(CPU)</option>
              <option value="precision">프리미엄(GPU)</option>
              <option value="auto">자동</option>
            </select>
          </div>
        </div>

        {/* OCR Mode Info */}
        <div className="p-4 bg-gray-50 rounded-lg text-sm">
          <p className="font-medium mb-2">OCR 모드 안내</p>
          <ul className="space-y-1 text-gray-600">
            <li>
              <strong>기본(CPU):</strong> 빠른 처리 속도, 대량 문서에 적합
            </li>
            <li>
              <strong>고급(CPU):</strong> AI 기반 높은 정확도, 일반 업무 문서 추천
            </li>
            <li>
              <strong>프리미엄(GPU):</strong> VLM 기반 최고 품질, 중요 문서/계약서 추천
            </li>
            <li>
              <strong>자동:</strong> 문서 특성에 따라 최적 모드 자동 선택
            </li>
          </ul>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!selectedFile || loading}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '업로드 중...' : '업로드 및 OCR 시작'}
        </button>
      </form>
    </div>
  );
}
