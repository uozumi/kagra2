import React from 'react';
import { TextField, LinearProgress, Box } from '@mui/material';
import type { TextFieldProps } from '@mui/material';

interface ValidatedTextFieldProps extends Omit<TextFieldProps, 'onChange'> {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
  showProgress?: boolean;
}

export const ValidatedTextField: React.FC<ValidatedTextFieldProps> = ({
  value,
  onChange,
  maxLength = 1000,
  showProgress = false,
  ...textFieldProps
}) => {
  // プログレスバーの値を計算
  const progress = (value.length / maxLength) * 100;

  // フィールドが上限に近づいているかをチェック
  const isNearLimit = value.length >= maxLength * 0.9 && value.length < maxLength;
  const isAtLimit = value.length === maxLength;
  const isOverLimit = value.length > maxLength;

  return (
    <Box>
      <TextField
        {...textFieldProps}
        value={value}
        onChange={(e) => {
          // 文字数制限を適用
          if (e.target.value.length <= maxLength) {
            onChange(e.target.value);
          }
        }}
        inputProps={{ 
          ...textFieldProps.inputProps,
          maxLength: maxLength 
        }}
        error={isOverLimit || textFieldProps.error}
        sx={{
          ...textFieldProps.sx,
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: isOverLimit ? 'error.main' : 
                           (isAtLimit || isNearLimit) ? 'warning.main' : 
                           'rgba(0, 0, 0, 0.23)'
            },
            '&:hover fieldset': {
              borderColor: isOverLimit ? 'error.main' : 
                           (isAtLimit || isNearLimit) ? 'warning.main' : 
                           'rgba(0, 0, 0, 0.23)'
            },
            '&.Mui-focused fieldset': {
              borderColor: isOverLimit ? 'error.main' : 
                           (isAtLimit || isNearLimit) ? 'warning.main' : 
                           'primary.main'
            }
          }
        }}
      />
      {showProgress && (
        <LinearProgress 
          variant="determinate" 
          value={progress}
          sx={{ 
            height: 3,
            borderRadius: 1,
            backgroundColor: 'rgba(0, 0, 0, 0.08)',
            opacity: 1,
            transition: 'opacity 0.2s ease',
            '& .MuiLinearProgress-bar': {
              transition: 'none',
              backgroundColor: isOverLimit ? 'error.main' : 
                            (isAtLimit || isNearLimit) ? 'warning.main' : 
                            'primary.main'
            }
          }}
        />
      )}
    </Box>
  );
}; 