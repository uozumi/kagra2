import React, { useEffect, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, CircularProgress, Box, FormControl, InputLabel, Select, MenuItem, Alert, Typography, Chip, LinearProgress } from '@mui/material';
import { nodeApi, blockApi } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';

interface NodeOption {
  id: string;
  title: string;
  is_public: boolean;
}

interface CreateThemeBlockProps {
  open: boolean;
  onClose: () => void;
  theme: { id: string; title: string };
  onSuccess?: () => void;
  titleMaxLength?: number;
  contentMaxLength?: number;
}

const CreateThemeBlock: React.FC<CreateThemeBlockProps> = ({ 
  open, 
  onClose, 
  theme, 
  onSuccess,
  titleMaxLength = 100,
  contentMaxLength = 400
}) => {
  const { user } = useAuth();
  const [blockTitle, setBlockTitle] = useState('');
  const [blockContent, setBlockContent] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [userNodes, setUserNodes] = useState<NodeOption[]>([]);
  const [saveLoading, setSaveLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // 文字数の状態判定
  const isTitleNearLimit = blockTitle.length >= titleMaxLength * 0.9 && blockTitle.length < titleMaxLength;
  const isTitleAtLimit = blockTitle.length === titleMaxLength;
  const isTitleOverLimit = blockTitle.length > titleMaxLength;
  
  const isContentNearLimit = blockContent.length >= contentMaxLength * 0.9 && blockContent.length < contentMaxLength;
  const isContentAtLimit = blockContent.length === contentMaxLength;
  const isContentOverLimit = blockContent.length > contentMaxLength;

  useEffect(() => {
    if (!open) return;
    const fetchNodes = async () => {
      if (!user) return;
      try {
        const data = await nodeApi.getNodes();
        setUserNodes(data || []);
        if (data && data.length > 0) {
          setSelectedNodeId(data[0].id);
        } else {
          setSelectedNodeId('');
        }
      } catch (error) {
        console.error('ノードの取得に失敗しました:', error);
      }
    };
    fetchNodes();
    setBlockTitle(theme.title || '');
    setBlockContent('');
    setFormError(null);
  }, [open, user, theme.title]);

  const handleCreateBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!blockTitle.trim() || !selectedNodeId) {
      setFormError('タイトルとノードを選択してください');
      return;
    }
    
    // バリデーション
    if (blockTitle.length > titleMaxLength) {
      setFormError(`タイトルは${titleMaxLength}文字以内にしてください`);
      return;
    }
    
    if (blockContent.length > contentMaxLength) {
      setFormError(`内容は${contentMaxLength}文字以内にしてください`);
      return;
    }
    
    setSaveLoading(true);
    try {
      await blockApi.createBlock({
        title: blockTitle.trim(),
        content: blockContent.trim(),
        node_id: selectedNodeId,
        block_theme_id: theme.id
      });
      
      if (onSuccess) onSuccess();
      onClose();
    } catch (error: any) {
      setFormError(error.message || '作成に失敗しました');
    } finally {
      setSaveLoading(false);
    }
  };

  // タイトル変更ハンドラー（文字数制限付き）
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= titleMaxLength) {
      setBlockTitle(value);
    }
  };

  // コンテンツ変更ハンドラー（文字数制限付き）
  const handleContentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= contentMaxLength) {
      setBlockContent(value);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '16px 24px'
      }}>
        <Typography variant="h6" component="div">
          新規作成
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose} disabled={saveLoading}>
            キャンセル
          </Button>
          <Button 
            onClick={handleCreateBlock} 
            variant="contained" 
            color="primary" 
            disabled={saveLoading}
          >
            {saveLoading ? <CircularProgress size={20} color="inherit" /> : '作成'}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box component="form" onSubmit={handleCreateBlock} noValidate>
          <Chip label={theme.title} size="small" variant="outlined" sx={{ mb: 2 }} />
          
          <Box sx={{ mb: 2 }}>
            <TextField
              required
              fullWidth
              label="タイトル"
              value={blockTitle}
              onChange={handleTitleChange}
              disabled={saveLoading}
              inputProps={{ maxLength: titleMaxLength }}
              error={isTitleOverLimit}
              sx={{ 
                mb: 0.5,
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: isTitleOverLimit ? 'error.main' : 
                                (isTitleAtLimit || isTitleNearLimit) ? 'warning.main' : 
                                'rgba(0, 0, 0, 0.23)'
                  },
                  '&:hover fieldset': {
                    borderColor: isTitleOverLimit ? 'error.main' : 
                                (isTitleAtLimit || isTitleNearLimit) ? 'warning.main' : 
                                'rgba(0, 0, 0, 0.23)'
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: isTitleOverLimit ? 'error.main' : 
                                (isTitleAtLimit || isTitleNearLimit) ? 'warning.main' : 
                                'primary.main'
                  }
                }
              }}
            />
            {/* タイトル文字数プログレスバー */}
            <LinearProgress 
              variant="determinate" 
              value={(blockTitle.length / titleMaxLength) * 100}
              sx={{ 
                height: 3,
                borderRadius: 1,
                backgroundColor: 'rgba(0, 0, 0, 0.08)',
                opacity: blockTitle.length > 0 ? 1 : 0,
                transition: 'opacity 0.2s ease',
                '& .MuiLinearProgress-bar': {
                  transition: 'none',
                  backgroundColor: isTitleOverLimit ? 'error.main' : 
                                  (isTitleAtLimit || isTitleNearLimit) ? 'warning.main' : 
                                  'primary.main'
                }
              }}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="内容"
              value={blockContent}
              onChange={handleContentChange}
              disabled={saveLoading}
              inputProps={{ maxLength: contentMaxLength }}
              error={isContentOverLimit}
              sx={{ 
                mb: 0.5,
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: isContentOverLimit ? 'error.main' : 
                                (isContentAtLimit || isContentNearLimit) ? 'warning.main' : 
                                'rgba(0, 0, 0, 0.23)'
                  },
                  '&:hover fieldset': {
                    borderColor: isContentOverLimit ? 'error.main' : 
                                (isContentAtLimit || isContentNearLimit) ? 'warning.main' : 
                                'rgba(0, 0, 0, 0.23)'
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: isContentOverLimit ? 'error.main' : 
                                (isContentAtLimit || isContentNearLimit) ? 'warning.main' : 
                                'primary.main'
                  }
                }
              }}
            />
            {/* コンテンツ文字数プログレスバー */}
            <LinearProgress 
              variant="determinate" 
              value={(blockContent.length / contentMaxLength) * 100}
              sx={{ 
                height: 3,
                borderRadius: 1,
                backgroundColor: 'rgba(0, 0, 0, 0.08)',
                opacity: 1,
                transition: 'opacity 0.2s ease',
                '& .MuiLinearProgress-bar': {
                  transition: 'none',
                  backgroundColor: isContentOverLimit ? 'error.main' : 
                                  (isContentAtLimit || isContentNearLimit) ? 'warning.main' : 
                                  'primary.main'
                }
              }}
            />
          </Box>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>ノード</InputLabel>
            <Select
              value={selectedNodeId}
              onChange={(e) => setSelectedNodeId(e.target.value)}
              disabled={saveLoading}
              label="ノード"
            >
              {userNodes.map((node) => (
                <MenuItem key={node.id} value={node.id}>
                  {node.title} {node.is_public ? '(公開)' : '(非公開)'}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {formError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {formError}
            </Alert>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default CreateThemeBlock; 