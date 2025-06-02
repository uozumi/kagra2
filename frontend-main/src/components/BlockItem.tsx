import React from 'react';
import { Box, Typography, TextField, IconButton, CircularProgress, Chip, Button, Tooltip, LinearProgress } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import LinkIcon from '@mui/icons-material/Link';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { Link as RouterLink } from 'react-router-dom';
import Linkify from 'react-linkify';
import type { Block, BlockTheme } from '../types';

interface BlockItemProps {
  block: Block;
  isEditable: boolean;
  isHovered: boolean;
  nodeId: string;
  userId: string | undefined;
  editStates: {[blockId: string]: { title: boolean; content: boolean }};
  editValues: {[blockId: string]: { title: string; content: string }};
  deleteLoading: string | null;
  themes: BlockTheme[];
  onEditStart: (blockId: string, field: 'title' | 'content', value: string) => void;
  onEditEnd: (blockId: string, field: 'title' | 'content') => void;
  onEditChange: (blockId: string, field: 'title' | 'content', value: string) => void;
  onDelete: (blockId: string) => void;
  onAddTheme: (blockId: string) => void;
  onRemoveTheme: (blockId: string) => void;
  onNavigateToTheme?: (themeId: string) => void;
  titleMaxLength?: number;
  contentMaxLength?: number;
}

export const BlockItem: React.FC<BlockItemProps> = ({
  block,
  isEditable,
  isHovered,
  nodeId,
  userId,
  editStates,
  editValues,
  deleteLoading,
  themes,
  onEditStart,
  onEditEnd,
  onEditChange,
  onDelete,
  onAddTheme,
  onRemoveTheme,
  onNavigateToTheme,
  titleMaxLength = 100,
  contentMaxLength = 400
}) => {
  // 現在のタイトルと内容の値（編集中の場合は編集値、そうでなければ元の値）
  const currentTitle = editStates[block.id]?.title 
    ? (editValues[block.id]?.title ?? block.title) 
    : (editValues[block.id]?.title ?? block.title);
    
  const currentContent = editStates[block.id]?.content 
    ? (editValues[block.id]?.content ?? block.content ?? '') 
    : (editValues[block.id]?.content ?? block.content ?? '');

  // プログレスバーの値を計算
  const titleProgress = (currentTitle.length / titleMaxLength) * 100;
  const contentProgress = (currentContent.length / contentMaxLength) * 100;

  // フィールドが上限に近づいているかをチェック
  const isTitleNearLimit = currentTitle.length >= titleMaxLength * 0.9 && currentTitle.length < titleMaxLength;
  const isTitleAtLimit = currentTitle.length === titleMaxLength;
  const isTitleOverLimit = currentTitle.length > titleMaxLength;
  
  const isContentNearLimit = currentContent.length >= contentMaxLength * 0.9 && currentContent.length < contentMaxLength;
  const isContentAtLimit = currentContent.length === contentMaxLength;
  const isContentOverLimit = currentContent.length > contentMaxLength;

  return (
    <Box sx={{ width: '100%' }}>
      {isEditable ? (
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            value={currentTitle}
            InputProps={{ 
              readOnly: !isEditable || !editStates[block.id]?.title,
            }}
            variant="outlined"
            onFocus={isEditable ? () => onEditStart(block.id, 'title', block.title) : undefined}
            onBlur={isEditable ? () => onEditEnd(block.id, 'title') : undefined}
            onChange={isEditable ? (e) => {
              // 文字数制限を適用
              if (e.target.value.length <= titleMaxLength) {
                onEditChange(block.id, 'title', e.target.value);
              }
            } : undefined}
            sx={{ 
              mb: 0.5, 
              fontWeight: 'bold',
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
            inputProps={{ maxLength: titleMaxLength }}
            error={isTitleOverLimit}
          />
          {/* タイトル文字数プログレスバー */}
          <LinearProgress 
            variant="determinate" 
            value={titleProgress}
            sx={{ 
              height: 3,
              borderRadius: 1,
              backgroundColor: 'rgba(0, 0, 0, 0.08)',
              opacity: editStates[block.id]?.title || currentTitle.length > 0 ? 1 : 0,
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
      ) : (
        <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
          {block.title}
        </Typography>
      )}
      
      {isEditable ? (
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            multiline
            minRows={4}
            value={currentContent}
            InputProps={{ 
              readOnly: !isEditable || !editStates[block.id]?.content 
            }}
            variant="outlined"
            onFocus={isEditable ? () => onEditStart(block.id, 'content', block.content ?? '') : undefined}
            onBlur={isEditable ? () => onEditEnd(block.id, 'content') : undefined}
            onChange={isEditable ? (e) => {
              // 文字数制限を適用
              if (e.target.value.length <= contentMaxLength) {
                onEditChange(block.id, 'content', e.target.value);
              }
            } : undefined}
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
            placeholder="ブロックの内容を入力してください（任意）"
            inputProps={{ maxLength: contentMaxLength }}
            error={isContentOverLimit}
          />
          {/* 内容文字数プログレスバー */}
          <LinearProgress 
            variant="determinate" 
            value={contentProgress}
            sx={{ 
              height: 3,
              borderRadius: 1,
              backgroundColor: 'rgba(0, 0, 0, 0.08)',
              opacity: editStates[block.id]?.content || currentContent.length > 0 ? 1 : 0,
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
      ) : (
        <Typography variant="body1" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>
          <Linkify componentDecorator={(decoratedHref, decoratedText, key) => (
            <a href={decoratedHref} target="_blank" rel="noopener noreferrer" key={key}>
              {decoratedText}
            </a>
          )}>
            {block.content || ''}
          </Linkify>
        </Typography>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, mt: 1 }}>
        <Box>
          {block.block_theme_id ? (
            <Chip
              label={themes.find(t => t.id === block.block_theme_id)?.title || '未定'}
              color="primary"
              clickable
              size="small"
              variant="outlined"
              onClick={() => onNavigateToTheme && onNavigateToTheme(block.block_theme_id!)}
              onDelete={isEditable ? (e) => {
                e.stopPropagation();
                onRemoveTheme(block.id);
              } : undefined}
              sx={{ '& .MuiChip-label': { cursor: 'pointer' } }}
            />
          ) : isEditable && (
            <Button size="small" variant="outlined" onClick={() => onAddTheme(block.id)}>
              ＋テーマを追加
            </Button>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {/* 時計アイコン */}
          {isEditable && isHovered && (
            <Tooltip title={`更新日: ${new Date(block.updated_at).toLocaleString('ja-JP')}`} arrow placement="top">
              <IconButton size="small" color="default" sx={{ mr: 1 }}>
                <AccessTimeIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}

          {/* リンクアイコン */}
          <IconButton
            component={RouterLink}
            to={`/charaxy/${nodeId}/${block.id}`}
            color="info"
            size="small"
            sx={{ 
              mr: 1,
              opacity: isHovered ? 1 : 0,
              visibility: isHovered ? 'visible' : 'hidden',
              transition: 'opacity 0.2s'
            }}
          >
            <LinkIcon />
          </IconButton>
          
          {/* 削除アイコン */}
          {block.user_id === userId && isEditable && (
            <IconButton 
              color="error" 
              size="small" 
              onClick={() => onDelete(block.id)} 
              disabled={deleteLoading === block.id}
              sx={{ 
                opacity: isHovered || deleteLoading === block.id ? 1 : 0,
                visibility: isHovered || deleteLoading === block.id ? 'visible' : 'hidden',
                transition: 'opacity 0.2s'
              }}
            >
              {deleteLoading === block.id ? <CircularProgress size={20} /> : <DeleteIcon />}
            </IconButton>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default BlockItem; 