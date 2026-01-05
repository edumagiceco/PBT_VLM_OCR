'use client';

import { useState, useEffect } from 'react';
import { Edit2, Save, X, ChevronDown, ChevronRight, Table, Type, List, Image } from 'lucide-react';
import type { DocumentPage, DocumentBlock } from '@/types/document';

interface BlockEditorProps {
  page: DocumentPage;
  selectedBlockId: number | null;
  onBlockSelect: (blockId: number | null) => void;
  onBlockUpdate: (blockId: number, text: string) => void;
}

export default function BlockEditor({
  page,
  selectedBlockId,
  onBlockSelect,
  onBlockUpdate,
}: BlockEditorProps) {
  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [editText, setEditText] = useState('');
  const [expandedBlocks, setExpandedBlocks] = useState<Set<number>>(new Set());

  const sortedBlocks = [...page.blocks].sort((a, b) => a.block_order - b.block_order);

  const handleEditStart = (block: DocumentBlock) => {
    setEditingBlockId(block.id);
    setEditText(block.text || '');
  };

  const handleEditSave = () => {
    if (editingBlockId) {
      onBlockUpdate(editingBlockId, editText);
      setEditingBlockId(null);
      setEditText('');
    }
  };

  const handleEditCancel = () => {
    setEditingBlockId(null);
    setEditText('');
  };

  const toggleExpand = (blockId: number) => {
    setExpandedBlocks(prev => {
      const next = new Set(prev);
      if (next.has(blockId)) {
        next.delete(blockId);
      } else {
        next.add(blockId);
      }
      return next;
    });
  };

  const getBlockIcon = (type: string) => {
    switch (type) {
      case 'table':
        return <Table className="w-4 h-4 text-green-600" />;
      case 'header':
        return <Type className="w-4 h-4 text-purple-600 font-bold" />;
      case 'list':
        return <List className="w-4 h-4 text-orange-600" />;
      case 'image':
        return <Image className="w-4 h-4 text-pink-600" />;
      default:
        return <Type className="w-4 h-4 text-blue-600" />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-250px)]">
      {/* Header */}
      <div className="px-4 py-3 border-b">
        <h3 className="font-medium">블록 목록</h3>
        <p className="text-sm text-gray-500">
          {page.blocks.length}개 블록 • 클릭하여 편집
        </p>
      </div>

      {/* Block List */}
      <div className="flex-1 overflow-y-auto">
        {sortedBlocks.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            OCR 결과가 없습니다
          </div>
        ) : (
          <div className="divide-y">
            {sortedBlocks.map(block => {
              const isSelected = selectedBlockId === block.id;
              const isEditing = editingBlockId === block.id;
              const isExpanded = expandedBlocks.has(block.id);
              const hasLongText = (block.text?.length || 0) > 100;

              return (
                <div
                  key={block.id}
                  className={`transition-colors ${
                    isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                >
                  {/* Block Header */}
                  <div
                    className="px-4 py-3 cursor-pointer flex items-start gap-3"
                    onClick={() => onBlockSelect(isSelected ? null : block.id)}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      {getBlockIcon(block.block_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-gray-500">
                          #{block.block_order + 1}
                        </span>
                        <span className="text-xs px-1.5 py-0.5 bg-gray-100 rounded capitalize">
                          {block.block_type}
                        </span>
                        {block.confidence && (
                          <span className="text-xs text-gray-400">
                            {(block.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>

                      {isEditing ? (
                        <div className="space-y-2">
                          <textarea
                            value={editText}
                            onChange={e => setEditText(e.target.value)}
                            className="w-full p-2 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            rows={4}
                            autoFocus
                            onClick={e => e.stopPropagation()}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={e => {
                                e.stopPropagation();
                                handleEditSave();
                              }}
                              className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                            >
                              <Save className="w-3 h-3" />
                              저장
                            </button>
                            <button
                              onClick={e => {
                                e.stopPropagation();
                                handleEditCancel();
                              }}
                              className="flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded hover:bg-gray-200"
                            >
                              <X className="w-3 h-3" />
                              취소
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          {block.block_type === 'table' && block.table_json ? (
                            <TablePreview tableJson={block.table_json} />
                          ) : (
                            <div className="text-sm text-gray-700">
                              {hasLongText && !isExpanded ? (
                                <>
                                  {block.text?.slice(0, 100)}...
                                  <button
                                    onClick={e => {
                                      e.stopPropagation();
                                      toggleExpand(block.id);
                                    }}
                                    className="ml-1 text-blue-600 hover:underline"
                                  >
                                    더 보기
                                  </button>
                                </>
                              ) : (
                                <>
                                  {block.text || '(빈 텍스트)'}
                                  {hasLongText && isExpanded && (
                                    <button
                                      onClick={e => {
                                        e.stopPropagation();
                                        toggleExpand(block.id);
                                      }}
                                      className="ml-1 text-blue-600 hover:underline"
                                    >
                                      접기
                                    </button>
                                  )}
                                </>
                              )}
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    {/* Edit Button */}
                    {!isEditing && (
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          handleEditStart(block);
                        }}
                        className="flex-shrink-0 p-1.5 hover:bg-gray-200 rounded"
                        title="편집"
                      >
                        <Edit2 className="w-4 h-4 text-gray-400" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer - Raw Text */}
      <div className="border-t p-4">
        <details className="text-sm">
          <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
            전체 텍스트 보기
          </summary>
          <div className="mt-2 p-3 bg-gray-50 rounded-lg max-h-40 overflow-y-auto text-xs font-mono whitespace-pre-wrap">
            {page.raw_text || '(텍스트 없음)'}
          </div>
        </details>
      </div>
    </div>
  );
}

function TablePreview({ tableJson }: { tableJson: Record<string, unknown> }) {
  const rows = (tableJson.rows as string[][]) || [];

  if (rows.length === 0) {
    return <div className="text-sm text-gray-400">(빈 테이블)</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse">
        <tbody>
          {rows.slice(0, 5).map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td
                  key={j}
                  className={`border px-2 py-1 ${
                    i === 0 ? 'bg-gray-100 font-medium' : ''
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 5 && (
        <div className="text-xs text-gray-400 mt-1">
          +{rows.length - 5}개 행 더 있음
        </div>
      )}
    </div>
  );
}
