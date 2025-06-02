import { useState } from 'react';
import { blockApi } from '../lib/api';
import type { Block } from '../types';

interface UseBlockSorterProps {
  onSuccess?: () => void;
  onError?: (message: string) => void;
}

export const useBlockSorter = ({ onSuccess, onError }: UseBlockSorterProps = {}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [sortableBlocks, setSortableBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // モーダルを開く
  const openModal = (blocks: Block[]) => {
    setSortableBlocks([...blocks]);
    setModalOpen(true);
  };

  // モーダルを閉じる
  const closeModal = () => {
    setModalOpen(false);
    setSortableBlocks([]);
    setDraggedIndex(null);
  };

  // ドラッグ開始
  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  // ドラッグ終了
  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  // ドラッグオーバー
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // ドラッグエンター
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // ドラッグリーブ
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // ドロップ
  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    
    if (draggedIndex === null || draggedIndex === dropIndex) return;

    const newBlocks = [...sortableBlocks];
    const draggedBlock = newBlocks[draggedIndex];
    
    // 要素を削除して新しい位置に挿入
    newBlocks.splice(draggedIndex, 1);
    newBlocks.splice(dropIndex, 0, draggedBlock);
    
    setSortableBlocks(newBlocks);
    setDraggedIndex(null);
  };

  // 順序を保存
  const saveOrder = async () => {
    try {
      setLoading(true);
      
      // 各ブロックのsort_orderを更新
      const updatePromises = sortableBlocks.map((block, index) => 
        blockApi.updateBlock(block.id, { sort_order: index })
      );
      
      await Promise.all(updatePromises);
      
      closeModal();
      if (onSuccess) onSuccess();
    } catch (error: any) {
      console.error('並べ替え保存エラー:', error);
      if (onError) onError('並べ替えの保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return {
    modalOpen,
    sortableBlocks,
    loading,
    draggedIndex,
    openModal,
    closeModal,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDragEnter,
    handleDragLeave,
    handleDrop,
    saveOrder
  };
}; 