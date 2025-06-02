import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Button, Alert, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Switch, FormControlLabel, IconButton, CircularProgress, Card, CardContent, CardActions, CardMedia, Grid, Chip, Snackbar, LinearProgress, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import SettingsIcon from '@mui/icons-material/Settings';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCharaxy } from '../../contexts/CharaxyContext';
import { supabase } from '../../lib/supabase';
import CharaxyFormModal from '../../components/modal/CharaxyFormModal';
import { nodeApi } from '../../lib/api';

interface Charaxy {
  id: string;
  title: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  user_id: string;
  is_public?: boolean;
}

const CharaxyList: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  const { triggerRefresh } = useCharaxy();
  const [charaxies, setCharaxies] = useState<Charaxy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCharaxy, setEditingCharaxy] = useState<Charaxy | null>(null);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [saveLoading, setSaveLoading] = useState(false);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [publicStatusLoading, setPublicStatusLoading] = useState<{[key: string]: boolean}>({});
  const [isPublic, setIsPublic] = useState(true);
  const [hoveredCardId, setHoveredCardId] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (authLoading) return;
    fetchCharaxies();
  }, [user, authLoading]);

  const fetchCharaxies = async () => {
    try {
      setLoading(true);
      setError(null);
      if (user) {
        console.debug('CharaxyList: キャラクシーの取得開始', { userId: user.id });
        
        const data = await nodeApi.getNodes();
        
        console.debug('CharaxyList: キャラクシー取得完了', { 
          count: data?.length || 0, 
          first: data?.length ? data[0] : null 
        });
        
        setCharaxies(data as Charaxy[]);
      } else {
        setCharaxies([]);
      }
    } catch (error: any) {
      console.error('CharaxyList: エラー発生', error);
      setError(error.message || 'データ取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('このキャラクシーを削除してもよろしいですか？')) return;
    setDeleteLoading(id);
    
    console.debug('CharaxyList: キャラクシー削除開始', { id });
    
    try {
      if (!user) throw new Error('削除するにはログインが必要です');
      
      await nodeApi.deleteNode(id);
      
      console.log('CharaxyList: キャラクシー削除成功', { id });
      
      // UI上のリストからも削除
      setCharaxies(charaxies.filter((c) => c.id !== id));
      
      triggerRefresh();
    } catch (error: any) {
      console.error('CharaxyList: 削除失敗', error);
      setError(error.message || '削除中にエラーが発生しました');
    } finally {
      setDeleteLoading(null);
    }
  };

  const openCreateModal = () => {
    // キャラクシーの数をチェック（上限は5）
    if (charaxies.length >= 5) {
      // 上限に達している場合はモーダルを開かずにエラーメッセージを表示
      setCreateError('キャラクシーの作成上限（5）に達しました。既存のキャラクシーを削除してから再試行してください。');
      return;
    }
    
    setModalMode('create');
    setEditingCharaxy(null);
    setModalOpen(true);
  };

  const openEditModal = (charaxy: Charaxy) => {
    setModalMode('edit');
    setEditingCharaxy(charaxy);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingCharaxy(null);
  };

  const handleSave = async (title: string, description: string, isPublic: boolean, charaxyId?: string) => {
    try {
      if (!user) throw new Error('キャラクシーを保存するにはログインが必要です');
      
      if (modalMode === 'edit' && charaxyId) {
        // 編集モード
        await nodeApi.updateNode(charaxyId, {
          title: title.trim(),
          description: description.trim() || undefined,
          is_public: isPublic
        });
      } else {
        // 新規作成モード
        await nodeApi.createNode({
          title: title.trim(),
          description: description.trim() || undefined,
          type: 'charaxy',
          is_public: isPublic
        });
      }
      
      await fetchCharaxies();
      triggerRefresh();
      
      return true;
    } catch (error: any) {
      setError(error.message || 'キャラクシーの保存中にエラーが発生しました');
      throw error;
    }
  };

  // 公開状態を切り替える関数
  const handleTogglePublic = async (charaxy: Charaxy) => {
    try {
      if (!user) throw new Error('公開状態を変更するにはログインが必要です');
      setPublicStatusLoading(prev => ({ ...prev, [charaxy.id]: true }));
      // 楽観的UI
      setCharaxies(prev => prev.map(c => c.id === charaxy.id ? { ...c, is_public: !charaxy.is_public } : c));
      await nodeApi.updateNode(charaxy.id, {
        is_public: !charaxy.is_public
      });
    } catch (error: any) {
      setError(error.message || '公開状態の更新中にエラーが発生しました');
    } finally {
      setPublicStatusLoading(prev => {
        const newState = { ...prev };
        delete newState[charaxy.id];
        return newState;
      });
    }
  };

  const handleCardClick = (charaxyId: string) => {
    navigate(`/charaxy/${charaxyId}`);
  };

  if (loading || authLoading) {
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
    <Container 
      maxWidth="lg" 
      sx={{ 
        mt: 4, 
        mb: 4, 
        ml: 0,
        mr: 'auto'
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          キャラクシー一覧
        </Typography>
        {user && (
          <Button
            variant="contained"
            color="primary"
            onClick={openCreateModal}
          >
            作成
          </Button>
        )}
      </Box>
      {user && charaxies.length === 0 ? (
        <Box mt={4} textAlign="center">
          <Alert severity="info" sx={{ mb: 2 }}>
            まだキャラクシーが作成されていません
          </Alert>
          <Typography variant="body1" sx={{ mb: 3 }}>
            「新規作成」ボタンをクリックして、最初のキャラクシーを作成しましょう！
          </Typography>
        </Box>
      ) : charaxies.length > 0 ? (
        <Grid container spacing={3}>
          {charaxies.map((charaxy) => (
            <Grid item xs={12} sm={6} md={6} key={charaxy.id}>
              <Card 
                elevation={3} 
                sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                onMouseEnter={() => setHoveredCardId(charaxy.id)}
                onMouseLeave={() => setHoveredCardId(null)}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1} width="100%">
                    <Typography 
                      variant="h6" 
                      component="h2" 
                      sx={{ 
                        fontWeight: 'bold',
                        mb: 1,
                        wordBreak: 'break-word'
                      }}
                    >
                      {charaxy.title}
                    </Typography>
                  </Box>
                  
                  <Typography 
                    variant="body2" 
                    color="text.secondary"
                    sx={{ 
                      minHeight: '3em',
                      mb: 2,
                      wordBreak: 'break-word',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {charaxy.description || '説明なし'}
                  </Typography>
                  
                  <Typography 
                    variant="caption" 
                    color="text.secondary"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    <AccessTimeIcon fontSize="small" sx={{ mr: 0.5, fontSize: '1rem' }} />
                    {new Date(charaxy.updated_at).toLocaleDateString('ja-JP')}
                  </Typography>
                </CardContent>
                
                <CardActions sx={{ justifyContent: 'flex-end', p: 2}}>                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    {/* 左側：公開状態の表示 */}
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Chip
                        label={charaxy.is_public ? '公開中' : '非公開'}
                        color={charaxy.is_public ? 'success' : 'default'}
                        size="small"
                        variant={charaxy.is_public ? 'filled' : 'outlined'}
                        sx={{ 
                          minWidth: '70px',
                          '& .MuiChip-label': { 
                            fontWeight: charaxy.is_public ? 'bold' : 'normal'
                          }
                        }}
                      />
                    </Box>
                    
                    {/* 右側：削除と編集ボタン */}
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {(hoveredCardId === charaxy.id || deleteLoading === charaxy.id) && (
                        <>
                          <IconButton
                            onClick={() => handleDelete(charaxy.id)}
                            color="error"
                            size="small"
                            disabled={deleteLoading === charaxy.id}
                            sx={{ 
                              opacity: hoveredCardId === charaxy.id ? 1 : 0,
                              transition: 'opacity 0.2s ease-in-out'
                            }}
                          >
                            {deleteLoading === charaxy.id ? <CircularProgress size={20} /> : <DeleteIcon />}
                          </IconButton>
                          <IconButton
                            color="secondary"
                            size="small"
                            onClick={() => openEditModal(charaxy)}
                            sx={{ 
                              opacity: hoveredCardId === charaxy.id ? 1 : 0,
                              transition: 'opacity 0.2s ease-in-out'
                            }}
                          >
                            <SettingsIcon />
                          </IconButton>
                        </>
                      )}
                      <Button
                        component={RouterLink}
                        to={`/charaxy/${charaxy.id}`}
                        color="primary"
                        variant="contained"
                        startIcon={<EditIcon />}
                        sx={{ ml: 1 }}
                      >
                        編集
                      </Button>
                    </Box>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : null}
      {/* 新規作成・編集用共通モーダル */}
      <CharaxyFormModal
        open={modalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
        titleMaxLength={100}
        descriptionMaxLength={400}
        mode={modalMode}
        charaxyData={editingCharaxy ? {
          id: editingCharaxy.id,
          title: editingCharaxy.title,
          description: editingCharaxy.description || '',
          is_public: !!editingCharaxy.is_public
        } : undefined}
      />
      <Snackbar
        open={!!createError}
        autoHideDuration={6000}
        onClose={() => setCreateError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setCreateError(null)}>
          {createError}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CharaxyList; 