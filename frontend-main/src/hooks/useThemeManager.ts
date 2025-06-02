import { useState, useEffect } from 'react';
import { blockApi } from '../lib/api';
import type { BlockTheme } from '../types';

interface UseThemeManagerProps {
  onSuccess?: () => void;
  onError?: (message: string) => void;
}

export const useThemeManager = ({ onSuccess, onError }: UseThemeManagerProps = {}) => {
  const [themes, setThemes] = useState<BlockTheme[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [themeLoading, setThemeLoading] = useState(false);
  const [newThemeTitle, setNewThemeTitle] = useState('');
  const [activeTab, setActiveTab] = useState(0);

  // テーマ一覧を取得
  const fetchThemes = async () => {
    try {
      setThemeLoading(true);
      // 仮実装：テーマAPIが実装されるまで空配列を返す
      setThemes([]);
    } catch (error: any) {
      console.error('テーマ取得エラー:', error);
      if (onError) onError('テーマの取得に失敗しました');
    } finally {
      setThemeLoading(false);
    }
  };

  // 初期化時にテーマを取得
  useEffect(() => {
    fetchThemes();
  }, []);

  // モーダルを開く
  const openModal = (blockId: string) => {
    setSelectedBlockId(blockId);
    setModalOpen(true);
    setActiveTab(0);
    setNewThemeTitle('');
  };

  // モーダルを閉じる
  const closeModal = () => {
    setModalOpen(false);
    setSelectedBlockId(null);
    setNewThemeTitle('');
  };

  // タイトル変更
  const handleTitleChange = (title: string) => {
    if (title.length <= 100) {
      setNewThemeTitle(title);
    }
  };

  // テーマを選択してブロックに追加
  const selectTheme = async (themeId: string) => {
    if (!selectedBlockId) return;

    try {
      setThemeLoading(true);
      
      await blockApi.updateBlock(selectedBlockId, {
        block_theme_id: themeId
      });

      closeModal();
      if (onSuccess) onSuccess();
    } catch (error: any) {
      console.error('テーマ追加エラー:', error);
      if (onError) onError('テーマの追加に失敗しました');
    } finally {
      setThemeLoading(false);
    }
  };

  // 新しいテーマを作成
  const addTheme = async () => {
    if (!newThemeTitle.trim() || !selectedBlockId) return;

    try {
      setThemeLoading(true);
      
      // 仮実装：テーマ作成APIが実装されるまでコメントアウト
      // const newTheme = await themeApi.createTheme({
      //   title: newThemeTitle.trim()
      // });
      
      // await blockApi.updateBlock(selectedBlockId, {
      //   block_theme_id: newTheme.id
      // });

      closeModal();
      if (onSuccess) onSuccess();
    } catch (error: any) {
      console.error('テーマ作成エラー:', error);
      if (onError) onError('テーマの作成に失敗しました');
    } finally {
      setThemeLoading(false);
    }
  };

  // ブロックからテーマを削除
  const removeTheme = async (blockId: string) => {
    try {
      setThemeLoading(true);
      
      await blockApi.updateBlock(blockId, {
        block_theme_id: undefined
      });

      if (onSuccess) onSuccess();
    } catch (error: any) {
      console.error('テーマ削除エラー:', error);
      if (onError) onError('テーマの削除に失敗しました');
    } finally {
      setThemeLoading(false);
    }
  };

  return {
    themes,
    modalOpen,
    selectedBlockId,
    themeLoading,
    newThemeTitle,
    activeTab,
    openModal,
    closeModal,
    handleTitleChange,
    selectTheme,
    addTheme,
    removeTheme,
    setActiveTab,
    fetchThemes
  };
}; 