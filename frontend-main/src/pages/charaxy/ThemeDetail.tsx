import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Typography, Box, CircularProgress, Alert, Paper, List, ListItem, ListItemText, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Snackbar, IconButton, LinearProgress } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import EditIcon from '@mui/icons-material/Edit';
import { useAuth } from '../../contexts/AuthContext';
import CreateThemeBlock from '../../components/modal/CreateThemeBlock';
import { nodeApi, themeApi } from '../../lib/api';
import type { BlockTheme, Block, Node } from '../../types';

const ThemeDetail: React.FC = () => {
  const { themeId } = useParams<{ themeId: string }>();
  const [theme, setTheme] = useState<BlockTheme | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [debug, setDebug] = useState<string[]>([]);
  const { user, session } = useAuth();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [writeModalOpen, setWriteModalOpen] = useState(false);
  const [noNodeAlertOpen, setNoNodeAlertOpen] = useState(false);
  
  // テーマ編集関連の状態
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editThemeTitle, setEditThemeTitle] = useState('');
  const [isHovered, setIsHovered] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);

  const fetchNodes = async () => {
    if (!user || !session?.access_token) return;
    
    try {
      const nodesData = await nodeApi.getNodes();
      setNodes(nodesData || []);
      // 初期選択肢を設定
      if (nodesData && nodesData.length > 0) {
        // 初期選択肢は設定しない（CreateThemeBlockで自動設定される）
      }
    } catch (error) {
      console.error('ノード取得エラー:', error);
    }
  };

  const fetchTheme = async () => {
    if (!themeId) return;
    
    try {
      const themeData = await themeApi.getTheme(themeId);
      setTheme(themeData);
      setEditThemeTitle(themeData.title || '');
    } catch (error) {
      console.error('テーマ取得エラー:', error);
      setError('テーマの取得に失敗しました');
    }
  };

  const fetchBlocks = async () => {
    if (!themeId) return;
    
    try {
      const blocksData = await themeApi.getThemeBlocks(themeId);
      setBlocks(blocksData || []);
    } catch (error) {
      console.error('ブロック取得エラー:', error);
      setError('ブロックの取得に失敗しました');
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      await Promise.all([
        fetchTheme(),
        fetchBlocks(),
        fetchNodes()
      ]);
      
      setLoading(false);
    };

    if (themeId && user && session?.access_token) {
      fetchData();
    }
  }, [themeId, user, session?.access_token]);

  const handleWriteClick = () => {
    if (nodes.length === 0) {
      setNoNodeAlertOpen(true);
      return;
    }
    setWriteModalOpen(true);
  };

  const handleBlockCreateSuccess = () => {
    fetchBlocks(); // ブロック一覧を再取得
  };

  const handleEditClick = () => {
    setEditModalOpen(true);
  };

  const handleSaveTheme = async () => {
    if (!themeId || !editThemeTitle.trim()) return;
    
    setSaveLoading(true);
    try {
      await themeApi.updateTheme(themeId, { title: editThemeTitle.trim() });
      
      // テーマ情報を再取得
      await fetchTheme();
      setEditModalOpen(false);
    } catch (error: any) {
      console.error('テーマ更新エラー:', error);
      setError(error.message || 'テーマの更新に失敗しました');
    } finally {
      setSaveLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!theme) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning">テーマが見つかりません</Alert>
      </Container>
    );
  }

  const isCreator = user && theme.creator_id === user.id;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* テーマタイトル */}
      <Box 
        sx={{ 
          mb: 4, 
          display: 'flex', 
          alignItems: 'center', 
          gap: 2,
          cursor: isCreator ? 'pointer' : 'default'
        }}
        onMouseEnter={() => isCreator && setIsHovered(true)}
        onMouseLeave={() => isCreator && setIsHovered(false)}
        onClick={isCreator ? handleEditClick : undefined}
      >
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {theme.title}
        </Typography>
        {isCreator && (
          <IconButton 
            size="small" 
            sx={{ 
              opacity: isHovered ? 1 : 0.3,
              transition: 'opacity 0.2s ease'
            }}
          >
            <EditIcon />
          </IconButton>
        )}
      </Box>

      {/* ブロック数とアクション */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          {blocks.length}件のブロック
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleWriteClick}
          sx={{ minWidth: 120 }}
        >
          このテーマで書く
        </Button>
      </Box>

      {/* ブロック一覧 */}
      {blocks.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            まだブロックがありません
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            「このテーマで書く」ボタンから最初のブロックを作成しましょう
          </Typography>
        </Paper>
      ) : (
        <List>
          {blocks.map((block) => (
            <ListItem 
              key={block.id} 
              component={RouterLink} 
              to={`/charaxy/nodes/${block.node_id}/blocks/${block.id}`}
              sx={{ 
                mb: 1, 
                border: 1, 
                borderColor: 'divider', 
                borderRadius: 1,
                textDecoration: 'none',
                color: 'inherit',
                '&:hover': {
                  backgroundColor: 'action.hover'
                }
              }}
            >
              <ListItemText
                primary={block.title}
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {block.node_title && `${block.node_title} • `}
                      {block.user_name && `${block.user_name} • `}
                      {new Date(block.updated_at).toLocaleDateString('ja-JP')}
                    </Typography>
                    {block.content && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        {block.content.length > 100 ? `${block.content.substring(0, 100)}...` : block.content}
                      </Typography>
                    )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      )}

      {/* デバッグ情報 */}
      {debug.length > 0 && (
        <Box sx={{ mt: 4, p: 2, backgroundColor: 'grey.100', borderRadius: 1 }}>
          <Typography variant="h6" gutterBottom>デバッグ情報</Typography>
          {debug.map((item, index) => (
            <Typography key={index} variant="body2" component="pre" sx={{ fontSize: '0.75rem' }}>
              {item}
            </Typography>
          ))}
        </Box>
      )}

      {/* ブロック追加モーダル */}
      <CreateThemeBlock
        open={writeModalOpen}
        onClose={() => setWriteModalOpen(false)}
        theme={{ id: themeId || '', title: theme?.title || '' }}
        onSuccess={handleBlockCreateSuccess}
        titleMaxLength={100}
        contentMaxLength={400}
      />

      {/* テーマ編集モーダル */}
      <Dialog open={editModalOpen} onClose={() => setEditModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>テーマを編集</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="テーマタイトル"
            fullWidth
            variant="outlined"
            value={editThemeTitle}
            onChange={(e) => setEditThemeTitle(e.target.value)}
            disabled={saveLoading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditModalOpen(false)} disabled={saveLoading}>
            キャンセル
          </Button>
          <Button onClick={handleSaveTheme} variant="contained" disabled={saveLoading || !editThemeTitle.trim()}>
            {saveLoading ? <CircularProgress size={20} /> : '保存'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ノードなしアラート */}
      <Snackbar
        open={noNodeAlertOpen}
        autoHideDuration={6000}
        onClose={() => setNoNodeAlertOpen(false)}
      >
        <Alert onClose={() => setNoNodeAlertOpen(false)} severity="warning">
          ブロックを作成するには、まずノードを作成してください
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ThemeDetail; 