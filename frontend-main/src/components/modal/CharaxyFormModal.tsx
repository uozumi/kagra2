import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, Button, Typography, Box, CircularProgress, FormControlLabel, Switch } from '@mui/material';
import { ValidatedTextField } from '../common/ValidatedTextField';

interface CharaxyData {
  id?: string;
  title: string;
  description: string;
  is_public: boolean;
}

interface CharaxyFormModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (title: string, description: string, isPublic: boolean, charaxyId?: string) => Promise<void | boolean>;
  titleMaxLength?: number;
  descriptionMaxLength?: number;
  mode: 'create' | 'edit';
  charaxyData?: CharaxyData;
}

const CharaxyFormModal: React.FC<CharaxyFormModalProps> = ({
  open,
  onClose,
  onSave,
  titleMaxLength = 100,
  descriptionMaxLength = 400,
  mode = 'create',
  charaxyData
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [titleError, setTitleError] = useState<string | null>(null);

  // モーダルが開かれたとき、または編集データが変更されたときに初期値をセット
  useEffect(() => {
    if (open && mode === 'edit' && charaxyData) {
      setTitle(charaxyData.title);
      setDescription(charaxyData.description || '');
      setIsPublic(charaxyData.is_public);
    } else if (open && mode === 'create') {
      // 新規作成モードの場合は初期化
      setTitle('');
      setDescription('');
      setIsPublic(true);
    }
    
    // エラー状態もリセット
    setTitleError(null);
  }, [open, mode, charaxyData]);

  const handleTitleChange = (value: string) => {
    setTitle(value);
  };

  const handleDescriptionChange = (value: string) => {
    setDescription(value);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // バリデーション
    if (!title.trim()) {
      setTitleError('タイトルは必須項目です');
      return;
    }
    
    if (title.length > titleMaxLength) {
      setTitleError(`タイトルは${titleMaxLength}文字以内にしてください`);
      return;
    }
    
    if (description.length > descriptionMaxLength) {
      setTitleError(`説明は${descriptionMaxLength}文字以内にしてください`);
      return;
    }
    
    setSaveLoading(true);
    try {
      // 編集モードの場合はキャラクシーIDを渡す
      await onSave(
        title.trim(), 
        description.trim(), 
        isPublic, 
        mode === 'edit' ? charaxyData?.id : undefined
      );
      // 成功したら入力フィールドをクリアしてモーダルを閉じる
      handleClose();
    } catch (error) {
      // エラーは親コンポーネントで処理
    } finally {
      setSaveLoading(false);
    }
  };

  const handleClose = () => {
    // モーダルを閉じる際に状態をリセット
    if (mode === 'create') {
      setTitle('');
      setDescription('');
      setIsPublic(true);
    }
    setTitleError(null);
    onClose();
  };

  // モーダルタイトルとボタンテキスト
  const modalTitle = mode === 'create' ? 'キャラクシー新規作成' : 'キャラクシー編集';
  const buttonText = mode === 'create' ? '作成' : '保存';

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '16px 24px'
      }}>
        <Typography variant="h6" component="div">
          {modalTitle}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={handleClose} disabled={saveLoading}>
            キャンセル
          </Button>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            color="primary" 
            disabled={saveLoading || !title.trim() || title.length > titleMaxLength || description.length > descriptionMaxLength}
          >
            {saveLoading ? <CircularProgress size={20} color="inherit" /> : buttonText}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box component="form" onSubmit={handleSave} noValidate>
          <ValidatedTextField
            required
            fullWidth
            id="title"
            label="タイトル"
            value={title}
            onChange={handleTitleChange}
            disabled={saveLoading}
            autoFocus
            maxLength={titleMaxLength}
            showProgress={true}
            sx={{ mb: 1 }}
          />
          {titleError && (
            <Typography variant="caption" color="error.main" sx={{ display: 'block', mb: 1 }}>
              {titleError}
            </Typography>
          )}
          
          <ValidatedTextField
            fullWidth
            id="description"
            label="説明"
            multiline
            rows={3}
            value={description}
            onChange={handleDescriptionChange}
            disabled={saveLoading}
            placeholder="キャラクシーの説明を入力してください（任意）"
            maxLength={descriptionMaxLength}
            showProgress={true}
            sx={{ mb: 2 }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                color="primary"
                disabled={saveLoading}
              />
            }
            label={isPublic ? '公開' : '非公開'}
          />
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default CharaxyFormModal; 