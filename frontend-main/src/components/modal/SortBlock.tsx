import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  List,
  ListItem,
  Typography,
  Box,
  CircularProgress,
  Paper
} from '@mui/material';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import type { Block } from '../../types';

interface SortBlockProps {
  open: boolean;
  blocks: Block[];
  loading: boolean;
  draggedIndex: number | null;
  onClose: () => void;
  onSave: () => void;
  onDragStart: (index: number) => void;
  onDragEnd: () => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragEnter: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, index: number) => void;
}

export const SortBlock: React.FC<SortBlockProps> = ({
  open,
  blocks,
  loading,
  draggedIndex,
  onClose,
  onSave,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '16px 24px'
      }}>
        <Typography variant="h6" component="div">
          ブロックの並べ替え
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose} disabled={loading}>
            キャンセル
          </Button>
          <Button 
            onClick={onSave}
            variant="contained"
            color="primary"
            disabled={loading}
          >
            {loading ? <CircularProgress size={20} color="inherit" /> : '保存'}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          ドラッグ&ドロップでブロックの順序を変更できます
        </Typography>
        
        <List>
          {blocks.map((block, index) => (
            <ListItem
              key={block.id}
              sx={{ 
                p: 0, 
                mb: 1,
                opacity: draggedIndex === index ? 0.5 : 1,
                transition: 'opacity 0.2s'
              }}
            >
              <Paper
                draggable
                onDragStart={() => onDragStart(index)}
                onDragEnd={onDragEnd}
                onDragOver={onDragOver}
                onDragEnter={onDragEnter}
                onDragLeave={onDragLeave}
                onDrop={(e) => onDrop(e, index)}
                sx={{
                  width: '100%',
                  p: 2,
                  cursor: 'grab',
                  '&:active': {
                    cursor: 'grabbing'
                  },
                  '&:hover': {
                    backgroundColor: 'action.hover'
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <DragIndicatorIcon color="action" />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ mb: 0.5 }}>
                      {block.title}
                    </Typography>
                    {block.content && (
                      <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical'
                        }}
                      >
                        {block.content}
                      </Typography>
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {index + 1}
                  </Typography>
                </Box>
              </Paper>
            </ListItem>
          ))}
        </List>
      </DialogContent>
    </Dialog>
  );
};

export default SortBlock; 