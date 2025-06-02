import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Container, Typography, Box, CircularProgress, Alert, List, ListItem, Button, Snackbar, Dialog, DialogTitle, DialogContent, DialogActions, Tabs, Tab, TextField, ListItemText, Tooltip } from '@mui/material';
import { supabase } from '../../lib/supabase';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import SortIcon from '@mui/icons-material/Sort';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { useAuth } from '../../contexts/AuthContext';
import { nodeApi, blockApi } from '../../lib/api';
import type { Block } from '../../types';
import { useBlockEditor } from '../../hooks/useBlockEditor';
import { useThemeManager } from '../../hooks/useThemeManager';
import { useBlockSorter } from '../../hooks/useBlockSorter';
import { BlockItem } from '../../components/BlockItem';
import SortBlock from '../../components/modal/SortBlock';
import CreateBlock from '../../components/modal/CreateBlock';
import LinkTheme from '../../components/modal/LinkTheme';

const CharaxyDetail: React.FC = () => {
  // 1. ルーティング関連フック
  const { nodeId, blockId } = useParams<{ nodeId: string; blockId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // 2. 認証関連
  const { user } = useAuth();
  
  // 3. カスタムフック
  const blockEditor = useBlockEditor({
    onSuccess: () => {
      setSaveSuccess(true);
      setSaveSnackbarOpen(true);
      fetchBlocks();
    },
    onError: (message) => {
      setErrorMessage(message);
      setSaveSuccess(false);
      setSaveSnackbarOpen(true);
    }
  });

  const themeManager = useThemeManager({
    onSuccess: () => {
      setSaveSuccess(true);
      setSaveSnackbarOpen(true);
      fetchBlocks();
    },
    onError: (message) => {
      setErrorMessage(message);
      setSaveSuccess(false);
      setSaveSnackbarOpen(true);
    }
  });

  const blockSorter = useBlockSorter({
    onSuccess: () => {
      setSaveSuccess(true);
      setSaveSnackbarOpen(true);
      fetchBlocks();
    },
    onError: (message) => {
      setErrorMessage(message);
      setSaveSuccess(false);
      setSaveSnackbarOpen(true);
    }
  });
  
  // 4. ノード関連の状態
  const [nodeTitle, setNodeTitle] = useState<string>('');
  const [nodeOwnerName, setNodeOwnerName] = useState<string>('');
  const [nodeUpdatedAt, setNodeUpdatedAt] = useState<string>('');
  const [isNodeOwner, setIsNodeOwner] = useState<boolean>(false);
  const [nodeOwnerAvatar, setNodeOwnerAvatar] = useState<string | null>(null);
  const [nodeOwnerAffiliations, setNodeOwnerAffiliations] = useState<{ tenantId: string, tenantName: string, departments: string[] }[]>([]);
  
  // 5. ブロック関連の状態
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [block, setBlock] = useState<Block | null>(null);
  const [blockTitle, setBlockTitle] = useState('');
  const [blockContent, setBlockContent] = useState('');
  const [editBlockId, setEditBlockId] = useState<string | null>(null);
  const [hoveredItemId, setHoveredItemId] = useState<string | null>(null);
  
  // 6. テーマ関連の状態
  const [themes, setThemes] = useState<any[]>([]);
  const [themeTab, setThemeTab] = useState(0);
  const [newThemeTitle, setNewThemeTitle] = useState('');
  
  // 7. UI状態
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [themeModalOpen, setThemeModalOpen] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [themeLoading, setThemeLoading] = useState(false);
  const [themeError, setThemeError] = useState<string | null>(null);
  
  // 8. メッセージ関連
  const [saveSnackbarOpen, setSaveSnackbarOpen] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string>('エラーが発生しました');
  
  // 9. 派生値
  const isEditable = location.pathname.includes('/edit/');
  
  // 10. アバター画像のエラーハンドリング
  const [avatarError, setAvatarError] = useState(false);

  useEffect(() => {
    if (nodeId) {
      fetchData();
    }
  }, [nodeId, user]);

  // 所属情報表示条件のデバッグ
  useEffect(() => {
    console.log('所属情報表示条件チェック:', {
      isEditable,
      nodeOwnerAffiliationsLength: nodeOwnerAffiliations.length,
      nodeOwnerAffiliations,
      shouldShow: !isEditable && nodeOwnerAffiliations.length > 0
    });
  }, [isEditable, nodeOwnerAffiliations]);

  // ノードとブロックの取得
  const fetchData = async () => {
    if (!nodeId) return;
    setLoading(true);
    setError(null);
    setAvatarError(false); // アバターエラー状態をリセット
    
    try {
      // ノード情報取得
      const nodeData = await nodeApi.getNode(nodeId);
      
      console.log('CharaxyDetail - 取得したノードデータ:', nodeData);
      
      if (nodeData) {
        setNodeTitle(nodeData.title);
        setNodeUpdatedAt(nodeData.updated_at);
        
        // 現在のユーザーがノードの所有者かどうかを確認
        if (user && nodeData.user_id === user.id) {
          setIsNodeOwner(true);
        }
        
        // ノードデータに既にユーザー情報が含まれている場合はそれを使用
        if (nodeData.user_name) {
          console.log('ノードデータからユーザー情報を取得:', {
            user_name: nodeData.user_name,
            user_avatar: nodeData.user_avatar,
            user_affiliations: nodeData.user_affiliations
          });
          
          setNodeOwnerName(nodeData.user_name);
          
          if (nodeData.user_avatar) {
            console.log('ノードデータからアバターを取得:', nodeData.user_avatar);
            // Google画像の場合はサイズパラメータを調整
            let avatarUrl = nodeData.user_avatar;
            if (avatarUrl.includes('googleusercontent.com')) {
              // サイズを小さくしてCORS問題を軽減
              avatarUrl = avatarUrl.replace(/=s\d+-c$/, '=s40-c');
            }
            setNodeOwnerAvatar(avatarUrl);
            setAvatarError(false);
          } else {
            console.log('アバター画像は見つかりませんでした');
            setNodeOwnerAvatar(null);
          }
          
          // ノードデータに所属情報が含まれている場合はそれを使用
          if (nodeData.user_affiliations) {
            console.log('ノードデータから所属情報を取得:', nodeData.user_affiliations);
            setNodeOwnerAffiliations(nodeData.user_affiliations);
          } else {
            console.log('所属情報が見つかりませんでした');
            setNodeOwnerAffiliations([]);
          }
        } else if (nodeData.user_id) {
          // フォールバック: ノードデータにユーザー情報がない場合
          console.log('ノードデータにユーザー情報がありません - ユーザーID:', nodeData.user_id);
          setNodeOwnerName('ユーザー');
          setNodeOwnerAvatar(null);
          setNodeOwnerAffiliations([]);
        } else {
          // user_idもない場合
          console.log('ユーザーIDが見つかりません');
          setNodeOwnerName('不明なユーザー');
          setNodeOwnerAvatar(null);
          setNodeOwnerAffiliations([]);
        }
      }
      
      // ブロック取得
      await fetchBlocks();
      
    } catch (error: any) {
      console.error('CharaxyDetail: データ取得エラー', error);
      setError(error.message || 'データ取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const fetchBlocks = async () => {
    if (!nodeId) return;
    
    try {
      if (blockId) {
        // 特定のブロック取得
        const blockData = await blockApi.getBlock(nodeId, blockId);
        setBlock(blockData);
      } else {
        // 全ブロック取得
        const blocksData = await blockApi.getBlocks(nodeId);
        setBlocks(blocksData || []);
      }
    } catch (error: any) {
      console.error('CharaxyDetail: ブロック取得エラー', error);
      setError(error.message || 'ブロック取得中にエラーが発生しました');
    }
  };

  const handleDeleteBlock = async (id: string) => {
    if (!window.confirm('このブロックを削除してもよろしいですか？')) return;
    setDeleteLoading(id);
    
    try {
      if (!user) throw new Error('削除するにはログインが必要です');
      
      // APIライブラリ経由でブロック削除
      await blockApi.deleteBlock(id);
      
      // UI上のリストからも削除
      setBlocks(blocks.filter((b) => b.id !== id));
      
      setSaveSuccess(true);
      setErrorMessage('ブロックを削除しました');
      setSaveSnackbarOpen(true);
    } catch (error: any) {
      console.error('CharaxyDetail: 削除失敗', error);
      setSaveSuccess(false);
      setErrorMessage(error.message || '削除中にエラーが発生しました');
      setSaveSnackbarOpen(true);
    } finally {
      setDeleteLoading(null);
    }
  };

  const openCreateModal = () => {
    setEditBlockId(null);
    setBlockTitle('');
    setBlockContent('');
    setModalOpen(true);
  };

  const openEditModal = (block: Block) => {
    setEditBlockId(block.id);
    setBlockTitle(block.title);
    setBlockContent(block.content || '');
    setModalOpen(true);
  };

  const handleTitleChange = (value: string) => {
    setBlockTitle(value);
  };

  const handleContentChange = (value: string) => {
    setBlockContent(value);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditBlockId(null);
    setBlockTitle('');
    setBlockContent('');
  };

  const handleSaveBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!blockTitle.trim() || !nodeId) return;
    
    setSaveLoading(true);
    
    try {
      if (!user) throw new Error('ブロックを保存するにはログインが必要です');
      
      if (editBlockId) {
        // 編集モード - APIライブラリ経由でブロック更新
        await blockApi.updateBlock(editBlockId, {
          title: blockTitle.trim(),
          content: blockContent.trim()
        });
      } else {
        // 新規作成モード - APIライブラリ経由でブロック作成
        await blockApi.createBlock({
          title: blockTitle.trim(),
          content: blockContent.trim(),
          node_id: nodeId
        });
      }
      
      // ブロック一覧を再取得
      await fetchBlocks();
      
      setModalOpen(false);
      setEditBlockId(null);
      setBlockTitle('');
      setBlockContent('');
      
      setSaveSuccess(true);
      setErrorMessage(editBlockId ? 'ブロックを更新しました' : 'ブロックを作成しました');
      setSaveSnackbarOpen(true);
    } catch (error: any) {
      console.error('CharaxyDetail: 保存失敗', error);
      setSaveSuccess(false);
      setErrorMessage(error.message || 'ブロックの保存中にエラーが発生しました');
      setSaveSnackbarOpen(true);
    } finally {
      setSaveLoading(false);
    }
  };

  const handleSwitchToEditMode = () => {
    navigate(`/charaxy/edit/${nodeId}`);
  };

  const handleSwitchToViewMode = () => {
    navigate(`/charaxy/${nodeId}`);
  };

  const handleCloseSnackbar = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') return;
    setSaveSnackbarOpen(false);
  };

  const handleNavigateToTheme = (themeId: string) => {
    navigate(`/charaxy/themes/${themeId}`);
  };

  const handleOpenThemeModal = () => {
    setThemeModalOpen(true);
  };

  const handleCloseThemeModal = () => {
    setThemeModalOpen(false);
    setNewThemeTitle('');
  };

  const handleSelectTheme = async (themeId: string) => {
    try {
      await themeManager.selectTheme(themeId);
      setThemeModalOpen(false);
    } catch (error: any) {
      console.error('テーマ選択エラー:', error);
      setThemeError(error.message);
    }
  };

  const handleAddTheme = async () => {
    if (!newThemeTitle.trim()) return;
    
    try {
      await themeManager.addTheme();
      setNewThemeTitle('');
      setThemeModalOpen(false);
    } catch (error: any) {
      console.error('テーマ追加エラー:', error);
      setThemeError(error.message);
    }
  };

  // blockIdがある場合もblocks配列に1件だけセットして共通ロジックで描画
  const displayBlocks = blockId && block ? [block] : blocks;

  if (loading) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      {/* スナックバー */}
      <Snackbar
        open={saveSnackbarOpen}
        autoHideDuration={saveSuccess ? 3000 : null}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          severity={saveSuccess ? "success" : "error"} 
          onClose={handleCloseSnackbar}
        >
          {saveSuccess ? '保存しました' : errorMessage}
        </Alert>
      </Snackbar>
      
      {/* ヘッダー */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>        
        <Typography variant="h4" gutterBottom>{nodeTitle || 'キャラクシー'}</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title={nodeOwnerName ? `${nodeOwnerName}のアバター` : 'ユーザーアバター'}>
            {nodeOwnerAvatar && !avatarError ? (
              <Box 
                component="img" 
                src={nodeOwnerAvatar} 
                alt={`${nodeOwnerName}のアバター`}
                referrerPolicy="no-referrer"
                onLoad={(e) => {
                  console.log('アバター画像読み込み成功 - URL:', nodeOwnerAvatar);
                  console.log('画像サイズ:', {
                    naturalWidth: (e.currentTarget as HTMLImageElement).naturalWidth,
                    naturalHeight: (e.currentTarget as HTMLImageElement).naturalHeight
                  });
                }}
                onError={(e) => {
                  console.error('アバター画像の読み込みエラー - URL:', nodeOwnerAvatar);
                  console.error('エラー詳細:', {
                    src: (e.currentTarget as HTMLImageElement).src,
                    naturalWidth: (e.currentTarget as HTMLImageElement).naturalWidth,
                    naturalHeight: (e.currentTarget as HTMLImageElement).naturalHeight,
                    complete: (e.currentTarget as HTMLImageElement).complete
                  });
                  setAvatarError(true);
                }}
                sx={{ 
                  width: 40, 
                  height: 40, 
                  borderRadius: '50%', 
                  mr: 2,
                  objectFit: 'cover',
                  border: '1px solid #e0e0e0'
                }} 
              />
            ) : (
              <Box 
                sx={{ 
                  width: 40, 
                  height: 40, 
                  borderRadius: '50%', 
                  mr: 2,
                  bgcolor: 'grey.300',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'grey.700',
                  fontWeight: 'bold'
                }}
              >
                {nodeOwnerName?.charAt(0) || '?'}
              </Box>
            )}
          </Tooltip>
          <Box>
            {nodeOwnerName && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                作成者: {nodeOwnerName}
              </Typography>
            )}
            {!isEditable && nodeOwnerAffiliations.length > 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                所属: {nodeOwnerAffiliations.map(aff => 
                  `${aff.tenantName}${aff.departments.length > 0 ? ` (${aff.departments.join(', ')})` : ''}`
                ).join(' / ')}
              </Typography>
            )}
            {nodeUpdatedAt && (
              <Tooltip title="最終更新日時">
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                  <AccessTimeIcon fontSize="small" sx={{ mr: 0.5 }} />
                  {new Date(nodeUpdatedAt).toLocaleDateString('ja-JP')}
                </Typography>
              </Tooltip>
            )}
          </Box>
        </Box>
      </Box>
      
      {/* 閲覧モードかつ所有者の場合は編集ボタンを表示 */}
      {!isEditable && isNodeOwner && (
        <Box sx={{ mb: 3 }}>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<EditIcon />} 
            onClick={handleSwitchToEditMode}
          >
            編集モード
          </Button>
        </Box>
      )}
      
      {/* 編集モードの場合は閲覧モードに戻るボタンと追加・並べ替えボタンを表示 */}
      {isEditable && (
        <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
          <Button 
            variant="outlined" 
            onClick={handleSwitchToViewMode}
          >
            閲覧モード
          </Button>
          
          {/* blockIdがない（一覧表示時）のみボタンを表示（編集モードのみ） */}
          {!blockId && (
            <>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />} 
                onClick={openCreateModal}
              >
                追加
              </Button>
              
              {/* 並べ替えボタン - ブロックが2つ以上ある場合のみ表示 */}
              {blocks.length > 1 && (
                <Button
                  variant="outlined"
                  color="secondary"
                  startIcon={<SortIcon />}
                  onClick={() => blockSorter.openModal(blocks)}
                >
                  並べ替え
                </Button>
              )}
            </>
          )}
        </Box>
      )}
      
      {/* ブロック一覧または詳細 */}
      <List>
        {displayBlocks.length > 0 ? (
          displayBlocks.map((b) => (
            <ListItem 
              key={b.id} 
              divider
              onMouseEnter={() => setHoveredItemId(b.id)}
              onMouseLeave={() => setHoveredItemId(null)}
              sx={{ py: 2, px: 0 }}  
            >
              <BlockItem
                block={b}
                isEditable={isEditable}
                isHovered={hoveredItemId === b.id}
                nodeId={nodeId!}
                userId={user?.id}
                editStates={blockEditor.editStates}
                editValues={blockEditor.editValues}
                deleteLoading={deleteLoading}
                themes={themeManager.themes}
                onEditStart={blockEditor.handleEditStart}
                onEditEnd={blockEditor.handleEditEnd}
                onEditChange={blockEditor.handleEditChange}
                onDelete={handleDeleteBlock}
                onAddTheme={(blockId) => {
                  // ブロックIDをセット
                  themeManager.openModal(blockId);
                  // モーダルを表示
                  setThemeModalOpen(true);
                }}
                onRemoveTheme={themeManager.removeTheme}
                onNavigateToTheme={handleNavigateToTheme}
                titleMaxLength={100}
                contentMaxLength={400}
              />
            </ListItem>
          ))
        ) : (
          <ListItem>
            <Box sx={{ width: '100%', textAlign: 'center', py: 4 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                ブロックが0件です
              </Alert>
              {isEditable && (
                <Typography variant="body1" sx={{ mb: 2 }}>
                  「追加」ボタンをクリックして、最初のブロックを作成しましょう！
                </Typography>
              )}
            </Box>
          </ListItem>
        )}
      </List>
      
      {/* blockIdがある（1件表示時）のみ「一覧に戻る」ボタンを表示 */}
      {blockId && (
        <Box sx={{ mt: 3 }}>
          <Button variant="outlined" onClick={() => navigate(`/charaxy/${nodeId}`)}>
            一覧に戻る
          </Button>
        </Box>
      )}
      
      {/* テーマ追加・選択モーダル */}
      <LinkTheme
        open={themeModalOpen}
        onClose={handleCloseThemeModal}
        themes={themeManager.themes}
        activeTab={themeTab}
        themeLoading={themeManager.themeLoading}
        themeError={themeError}
        newThemeTitle={newThemeTitle}
        onTabChange={setThemeTab}
        onTitleChange={(title) => {
          // 100文字までの制限
          if (title.length <= 100) {
            setNewThemeTitle(title);
            // themeManagerにも値を反映
            themeManager.handleTitleChange(title);
          }
        }}
        onAddTheme={handleAddTheme}
        onSelectTheme={handleSelectTheme}
      />
      
      {/* 並べ替えモーダル */}
      <SortBlock
        open={blockSorter.modalOpen}
        blocks={blockSorter.sortableBlocks}
        loading={blockSorter.loading}
        draggedIndex={blockSorter.draggedIndex}
        onClose={blockSorter.closeModal}
        onSave={blockSorter.saveOrder}
        onDragStart={blockSorter.handleDragStart}
        onDragEnd={blockSorter.handleDragEnd}
        onDragOver={blockSorter.handleDragOver}
        onDragEnter={blockSorter.handleDragEnter}
        onDragLeave={blockSorter.handleDragLeave}
        onDrop={blockSorter.handleDrop}
      />
      
      {/* 新規作成・編集用モーダル（編集可のみ） */}
      {isEditable && (
        <CreateBlock
          open={modalOpen}
          onClose={handleCloseModal}
          title={blockTitle}
          content={blockContent}
          isEditing={!!editBlockId}
          loading={saveLoading}
          onTitleChange={handleTitleChange}
          onContentChange={handleContentChange}
          onSave={handleSaveBlock}
          titleMaxLength={100}
          contentMaxLength={400}
        />
      )}
    </Container>
  );
};

export default CharaxyDetail; 