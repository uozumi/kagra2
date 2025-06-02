import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  Tabs,
  Tab,
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  TextField,
  CircularProgress,
  Alert,
  Typography,
  LinearProgress
} from '@mui/material';
import type { BlockTheme } from '../../types';

interface LinkThemeProps {
  open: boolean;
  onClose: () => void;
  themes: BlockTheme[];
  activeTab: number;
  themeLoading: boolean;
  themeError: string | null;
  newThemeTitle: string;
  onTabChange: (tab: number) => void;
  onTitleChange: (title: string) => void;
  onAddTheme: () => void;
  onSelectTheme: (themeId: string) => void;
}

export const LinkTheme: React.FC<LinkThemeProps> = ({
  open,
  onClose,
  themes,
  activeTab,
  themeLoading,
  themeError,
  newThemeTitle,
  onTabChange,
  onTitleChange,
  onAddTheme,
  onSelectTheme
}) => {
  // 文字数制限
  const titleMaxLength = 100;
  
  // 文字数の状態判定
  const isTitleNearLimit = newThemeTitle.length >= titleMaxLength * 0.9 && newThemeTitle.length < titleMaxLength;
  const isTitleAtLimit = newThemeTitle.length === titleMaxLength;
  const isTitleOverLimit = newThemeTitle.length > titleMaxLength;
  
  // プログレスバーの値を計算
  const titleProgress = (newThemeTitle.length / titleMaxLength) * 100;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '16px 24px'
      }}>
        <Typography variant="h6" component="div">
          テーマ
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose} disabled={themeLoading}>
            {activeTab === 0 ? '閉じる' : 'キャンセル'}
          </Button>
          {activeTab === 1 && (
            <Button 
              onClick={onAddTheme}
              variant="contained"
              color="primary"
              disabled={themeLoading || !newThemeTitle.trim() || isTitleOverLimit}
            >
              {themeLoading ? <CircularProgress size={20} color="inherit" /> : '追加'}
            </Button>
          )}
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Tabs value={activeTab} onChange={(_, newValue) => onTabChange(newValue)}>
          <Tab label="テーマを選ぶ" />
          <Tab label="新たなテーマ" />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {activeTab === 0 ? (
            // 既存のテーマタブ
            <Box>
              {themeLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : themes.length === 0 ? (
                <Alert severity="info">
                  テーマがありません。新しいテーマを作成してください。
                </Alert>
              ) : (
                <List>
                  {themes.map((theme) => (
                    <ListItem key={theme.id} disablePadding>
                      <ListItemButton onClick={() => onSelectTheme(theme.id)}>
                        <ListItemText primary={theme.title} />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          ) : (
            // 新しいテーマタブ
            <Box>
              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label="新しいテーマ名"
                  value={newThemeTitle}
                  onChange={e => onTitleChange(e.target.value)}
                  disabled={themeLoading}
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
                {/* テーマ名文字数プログレスバー */}
                <LinearProgress 
                  variant="determinate" 
                  value={titleProgress}
                  sx={{ 
                    height: 3,
                    borderRadius: 1,
                    backgroundColor: 'rgba(0, 0, 0, 0.08)',
                    opacity: newThemeTitle.length > 0 ? 1 : 0,
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
              {themeError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {themeError}
                </Alert>
              )}
            </Box>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default LinkTheme; 