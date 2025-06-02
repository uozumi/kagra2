import React from 'react';
import { Dialog, DialogTitle, DialogContent, Button, CircularProgress, Box, Typography, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { ValidatedTextField } from '../common/ValidatedTextField';

interface Node {
  id: string;
  title: string;
}

interface CreateBlockProps {
  open: boolean;
  onClose: () => void;
  title: string;
  content: string;
  isEditing: boolean;
  loading: boolean;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
  onSave: (e: React.FormEvent) => Promise<void>;
  titleMaxLength?: number;
  contentMaxLength?: number;
  nodes?: Node[];
  selectedNodeId?: string;
  onNodeChange?: (nodeId: string) => void;
  showNodeSelector?: boolean;
}

export const CreateBlock: React.FC<CreateBlockProps> = ({
  open,
  onClose,
  title,
  content,
  isEditing,
  loading,
  onTitleChange,
  onContentChange,
  onSave,
  titleMaxLength = 100,
  contentMaxLength = 400,
  nodes = [],
  selectedNodeId = '',
  onNodeChange,
  showNodeSelector = false
}) => {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '16px 24px'
      }}>
        <Typography variant="h6" component="div">
          {isEditing ? 'ブロックを編集' : '新しいブロックを追加'}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose} disabled={loading}>
            キャンセル
          </Button>
          <Button 
            onClick={onSave} 
            variant="contained" 
            color="primary" 
            disabled={loading || !title.trim() || (showNodeSelector && !selectedNodeId)}
          >
            {loading ? <CircularProgress size={20} color="inherit" /> : (isEditing ? '更新' : '作成')}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box component="form" onSubmit={onSave} noValidate>
          <Box sx={{ mb: 2 }}>
            <ValidatedTextField
              autoFocus={true}
              margin="dense"
              label="タイトル"
              fullWidth
              value={title}
              onChange={onTitleChange}
              disabled={loading}
              required
              maxLength={titleMaxLength}
              showProgress={true}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <ValidatedTextField
              margin="dense"
              label="内容"
              multiline
              rows={10}
              fullWidth
              value={content}
              onChange={onContentChange}
              disabled={loading}
              maxLength={contentMaxLength}
              showProgress={true}
            />
          </Box>

          {/* ノード選択を最下部に移動 */}
          {showNodeSelector && nodes.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel id="node-select-label">キャラクシーを選択</InputLabel>
                <Select
                  labelId="node-select-label"
                  value={selectedNodeId}
                  label="キャラクシーを選択"
                  onChange={(e) => onNodeChange?.(e.target.value)}
                  disabled={loading}
                >
                  {nodes.map((node) => (
                    <MenuItem key={node.id} value={node.id}>
                      {node.title}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default CreateBlock; 