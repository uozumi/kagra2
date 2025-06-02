import { useState } from 'react';
import { blockApi } from '../lib/api';
import type { Block, EditState, EditValue } from '../types';

interface UseBlockEditorProps {
  onSuccess?: () => void;
  onError?: (message: string) => void;
}

export const useBlockEditor = ({ onSuccess, onError }: UseBlockEditorProps = {}) => {
  const [editStates, setEditStates] = useState<{[blockId: string]: EditState}>({});
  const [editValues, setEditValues] = useState<{[blockId: string]: EditValue}>({});
  const [saveLoading, setSaveLoading] = useState(false);

  // 編集開始
  const handleEditStart = (blockId: string, field: 'title' | 'content', value: string) => {
    setEditStates((prev) => ({
      ...prev,
      [blockId]: { ...prev[blockId], [field]: true }
    }));
    setEditValues((prev) => ({
      ...prev,
      [blockId]: { ...prev[blockId], [field]: value }
    }));
  };
  
  // 編集終了（保存）
  const handleEditEnd = async (blockId: string, field: 'title' | 'content') => {
    const newValue = editValues[blockId]?.[field];
    if (newValue === undefined) return;
    
    // タイトルが空の場合はエラーを表示して保存しない
    if (field === 'title' && !newValue.trim()) {
      if (onError) onError('タイトルは必須項目です。入力してから再度保存してください。');
      return;
    }
    
    try {
      setSaveLoading(true);
      
      // バリデーション
      if (field === 'title' && newValue.length > 100) {
        throw new Error('タイトルは100文字以内にしてください');
      }
      
      if (field === 'content' && newValue.length > 400) {
        throw new Error('内容は400文字以内にしてください');
      }
      
      // 編集状態フラグを解除
      setEditStates((prev) => ({
        ...prev,
        [blockId]: { ...prev[blockId], [field]: false }
      }));
      
      // 更新オブジェクトを作成
      const updateObj: any = {};
      updateObj[field] = newValue;
      
      // APIで更新
      await blockApi.updateBlock(blockId, updateObj);
      
      // 成功したら成功コールバックを呼び出す
      if (onSuccess) onSuccess();
    } catch (error: any) {
      // エラー時は編集状態に戻す
      setEditStates((prev) => ({
        ...prev,
        [blockId]: { ...prev[blockId], [field]: true }
      }));
      
      if (onError) onError(error.message || '保存中にエラーが発生しました');
    } finally {
      setSaveLoading(false);
    }
  };
  
  // 値変更
  const handleEditChange = (blockId: string, field: 'title' | 'content', value: string) => {
    setEditValues((prev) => ({
      ...prev,
      [blockId]: { ...prev[blockId], [field]: value }
    }));
  };

  // ブロック作成
  const createBlock = async (nodeId: string, userId: string | undefined, title: string, content: string, sortOrder: number = 0) => {
    if (!title.trim()) {
      if (onError) onError('タイトルは必須です');
      return null;
    }
    
    // バリデーション
    if (title.length > 100) {
      if (onError) onError('タイトルは100文字以内にしてください');
      return null;
    }
    
    if (content.length > 400) {
      if (onError) onError('内容は400文字以内にしてください');
      return null;
    }

    try {
      setSaveLoading(true);
      
      // 新規作成するブロックデータ
      const newBlock = { 
        title: title.trim(), 
        content: content.trim(), 
        node_id: nodeId, 
        sort_order: sortOrder
      };
      
      // APIで保存
      const data = await blockApi.createBlock(newBlock);
      
      // 成功コールバック
      if (onSuccess) onSuccess();
      
      return data as Block;
    } catch (error: any) {
      if (onError) onError(error.message || '保存中にエラーが発生しました');
      return null;
    } finally {
      setSaveLoading(false);
    }
  };

  // ブロック更新
  const updateBlock = async (blockId: string, title: string, content: string) => {
    if (!title.trim()) {
      if (onError) onError('タイトルは必須です');
      return false;
    }
    
    // バリデーション
    if (title.length > 100) {
      if (onError) onError('タイトルは100文字以内にしてください');
      return false;
    }
    
    if (content.length > 400) {
      if (onError) onError('内容は400文字以内にしてください');
      return false;
    }

    try {
      setSaveLoading(true);
      
      // 楽観的UI更新
      setEditValues((prev) => ({
        ...prev,
        [blockId]: { 
          ...prev[blockId], 
          title: title.trim(),
          content: content.trim()
        }
      }));
      
      // APIで保存
      await blockApi.updateBlock(blockId, { 
        title: title.trim(), 
        content: content.trim() 
      });
      
      if (onSuccess) onSuccess();
      return true;
    } catch (error: any) {
      if (onError) onError(error.message || '保存中にエラーが発生しました');
      return false;
    } finally {
      setSaveLoading(false);
    }
  };

  // ブロック削除
  const deleteBlock = async (blockId: string) => {
    try {
      setSaveLoading(true);
      
      await blockApi.deleteBlock(blockId);
      
      if (onSuccess) onSuccess();
      return true;
    } catch (error: any) {
      if (onError) onError(error.message || '削除中にエラーが発生しました');
      return false;
    } finally {
      setSaveLoading(false);
    }
  };

  return {
    editStates,
    editValues,
    saveLoading,
    handleEditStart,
    handleEditEnd,
    handleEditChange,
    createBlock,
    updateBlock,
    deleteBlock
  };
}; 