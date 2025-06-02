import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, CircularProgress, Box, Typography } from '@mui/material';
import { LinearProgress } from '@mui/material';

interface CreateThemeProps {
  open: boolean;
  onClose: () => void;
  onSave: (title: string) => Promise<void>;
  initialTitle?: string;
  maxLength?: number;
}

const CreateTheme: React.FC<CreateThemeProps> = ({
  open,
  onClose,
  onSave,
  initialTitle = '',
  maxLength = 50
}) => {
  const [title, setTitle] = useState(initialTitle);
  const [loading, setLoading] = useState(false);

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(e.target.value.slice(0, maxLength));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || title.length > maxLength) return;
    
    setLoading(true);
    try {
      await onSave(title);
      setTitle('');
    } catch (error) {
      console.error('テーマ保存エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setTitle('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '16px 24px'
      }}>
        <Typography variant="h6" component="div">
          テーマを作成
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={handleClose} disabled={loading}>
            キャンセル
          </Button>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            color="primary" 
            disabled={loading || !title.trim() || title.length > maxLength}
          >
            {loading ? <CircularProgress size={20} color="inherit" /> : '作成'}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box component="form" onSubmit={handleSave} noValidate>
          <Box sx={{ width: '100%', mb: 2 }}>
            <TextField
              required
              fullWidth
              id="theme-title"
              label="タイトル"
              value={title}
              onChange={handleTitleChange}
              disabled={loading}
              autoFocus
              inputProps={{ maxLength }}
              error={title.length > maxLength}
              sx={{ mb: 0.5 }}
            />
            <LinearProgress 
              variant="determinate" 
              value={(title.length / maxLength) * 100}
              sx={{ 
                height: 3,
                borderRadius: 1,
                backgroundColor: 'rgba(0, 0, 0, 0.08)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: title.length >= maxLength ? 'warning.main' : 
                                   title.length >= maxLength * 0.9 ? 'warning.light' : 
                                   'primary.main'
                }
              }}
            />
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTheme; 