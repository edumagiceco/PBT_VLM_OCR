'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCw, Maximize2, Minimize2 } from 'lucide-react';
import type { DocumentPage, DocumentBlock } from '@/types/document';

interface PageViewerProps {
  documentId: number;
  page: DocumentPage;
  selectedBlockId: number | null;
  onBlockSelect: (blockId: number | null) => void;
}

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000/api/v1`;
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
};

type FitMode = 'width' | 'height' | 'manual';

export default function PageViewer({
  documentId,
  page,
  selectedBlockId,
  onBlockSelect,
}: PageViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [fitMode, setFitMode] = useState<FitMode>('width');
  const [showOverlay, setShowOverlay] = useState(true);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  // 컨테이너 크기 측정
  useEffect(() => {
    const updateContainerSize = () => {
      if (containerRef.current) {
        setContainerSize({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateContainerSize();
    window.addEventListener('resize', updateContainerSize);
    return () => window.removeEventListener('resize', updateContainerSize);
  }, []);

  useEffect(() => {
    // 백엔드 프록시를 통해 이미지 URL 생성 (MinIO presigned URL 대신 직접 프록시 사용)
    const proxyUrl = `${getApiBaseUrl()}/files/documents/${documentId}/pages/${page.page_no}/image`;
    setImageUrl(proxyUrl);
    setLoading(false);
  }, [documentId, page.page_no]);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ width: img.naturalWidth, height: img.naturalHeight });
  };

  // 실제 적용할 줌 계산
  const calculateEffectiveZoom = useCallback(() => {
    if (imageSize.width === 0 || imageSize.height === 0) return zoom;
    if (containerSize.width === 0 || containerSize.height === 0) return zoom;

    if (fitMode === 'width') {
      return (containerSize.width - 40) / imageSize.width; // 40px 여백
    } else if (fitMode === 'height') {
      return (containerSize.height - 40) / imageSize.height;
    }
    return zoom;
  }, [fitMode, zoom, imageSize, containerSize]);

  const effectiveZoom = calculateEffectiveZoom();

  const handleZoomIn = () => {
    setFitMode('manual');
    setZoom(prev => Math.min(prev + 0.25, 5));
  };
  const handleZoomOut = () => {
    setFitMode('manual');
    setZoom(prev => Math.max(prev - 0.25, 0.25));
  };
  const handleFitWidth = () => setFitMode('width');
  const handleFitHeight = () => setFitMode('height');

  const getBlockColor = (block: DocumentBlock) => {
    const colors: Record<string, string> = {
      text: 'border-blue-500 bg-blue-500/10',
      header: 'border-purple-500 bg-purple-500/10',
      table: 'border-green-500 bg-green-500/10',
      list: 'border-orange-500 bg-orange-500/10',
      image: 'border-pink-500 bg-pink-500/10',
      footer: 'border-gray-500 bg-gray-500/10',
    };
    return colors[block.block_type] || colors.text;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">
            {page.page_no} / {page.page_no} 페이지
          </span>
          {page.confidence && (
            <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
              신뢰도: {(page.confidence * 100).toFixed(1)}%
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className={`px-3 py-1 text-sm rounded ${
              showOverlay
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            블록 표시
          </button>
          <div className="h-4 w-px bg-gray-200 mx-2" />
          <button
            onClick={handleFitWidth}
            className={`px-2 py-1 text-xs rounded ${
              fitMode === 'width'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="너비 맞춤"
          >
            너비
          </button>
          <button
            onClick={handleFitHeight}
            className={`px-2 py-1 text-xs rounded ${
              fitMode === 'height'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="높이 맞춤"
          >
            높이
          </button>
          <div className="h-4 w-px bg-gray-200 mx-1" />
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-gray-100 rounded"
            title="축소"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-sm w-14 text-center">{Math.round(effectiveZoom * 100)}%</span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-gray-100 rounded"
            title="확대"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Image Container */}
      <div
        ref={containerRef}
        className="relative overflow-auto bg-gray-100"
        style={{ height: 'calc(100vh - 200px)' }}
      >
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <RotateCw className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : imageUrl ? (
          <div
            className="relative inline-block p-4"
            style={{
              transform: `scale(${effectiveZoom})`,
              transformOrigin: 'top left',
            }}
          >
            <img
              src={imageUrl}
              alt={`Page ${page.page_no}`}
              className="max-w-none"
              onLoad={handleImageLoad}
            />

            {/* Block Overlays */}
            {showOverlay && imageSize.width > 0 && (
              <div
                className="absolute inset-0"
                style={{
                  width: imageSize.width,
                  height: imageSize.height,
                }}
              >
                {page.blocks.map(block => {
                  if (!block.bbox || block.bbox.length < 4) return null;

                  const [x1, y1, x2, y2] = block.bbox;
                  const isSelected = selectedBlockId === block.id;

                  return (
                    <div
                      key={block.id}
                      className={`absolute border-2 cursor-pointer transition-all ${
                        isSelected
                          ? 'border-red-500 bg-red-500/20 ring-2 ring-red-500'
                          : getBlockColor(block)
                      }`}
                      style={{
                        left: `${x1 * 100}%`,
                        top: `${y1 * 100}%`,
                        width: `${(x2 - x1) * 100}%`,
                        height: `${(y2 - y1) * 100}%`,
                      }}
                      onClick={() => onBlockSelect(isSelected ? null : block.id)}
                      title={`${block.block_type}: ${block.text?.slice(0, 50)}...`}
                    >
                      <div className="absolute -top-5 left-0 text-xs px-1 bg-white rounded shadow">
                        {block.block_order + 1}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
            이미지를 불러올 수 없습니다
          </div>
        )}
      </div>

      {/* Block Type Legend */}
      {showOverlay && (
        <div className="px-4 py-2 border-t flex items-center gap-4 text-xs">
          <span className="text-gray-500">블록 타입:</span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 border-2 border-blue-500 bg-blue-500/20 rounded" />
            텍스트
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 border-2 border-purple-500 bg-purple-500/20 rounded" />
            헤더
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 border-2 border-green-500 bg-green-500/20 rounded" />
            테이블
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 border-2 border-orange-500 bg-orange-500/20 rounded" />
            리스트
          </span>
        </div>
      )}
    </div>
  );
}
