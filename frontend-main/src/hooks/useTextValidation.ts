export interface UseTextValidationReturn {
  isNearLimit: boolean;
  isAtLimit: boolean;
  isOverLimit: boolean;
  progress: number;
  getBorderColor: () => string;
  getProgressColor: () => string;
  getFieldSx: () => object;
}

/**
 * 文字数制限の状態判定ロジックを共通化するカスタムフック
 * @param text 対象のテキスト
 * @param maxLength 最大文字数
 */
export const useTextValidation = (text: string, maxLength: number): UseTextValidationReturn => {
  const isNearLimit = text.length >= maxLength * 0.9 && text.length < maxLength;
  const isAtLimit = text.length === maxLength;
  const isOverLimit = text.length > maxLength;
  
  const getBorderColor = (): string => {
    if (isOverLimit) return 'error.main';
    if (isAtLimit || isNearLimit) return 'warning.main';
    return 'rgba(0, 0, 0, 0.23)';
  };
  
  const getProgressColor = (): string => {
    if (isOverLimit) return 'error.main';
    if (isAtLimit || isNearLimit) return 'warning.main';
    return 'primary.main';
  };
  
  const getFieldSx = () => ({
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor: getBorderColor()
      },
      '&:hover fieldset': {
        borderColor: getBorderColor()
      },
      '&.Mui-focused fieldset': {
        borderColor: isOverLimit ? 'error.main' : 
                     (isAtLimit || isNearLimit) ? 'warning.main' : 
                     'primary.main'
      }
    }
  });
  
  return {
    isNearLimit,
    isAtLimit,
    isOverLimit,
    progress: (text.length / maxLength) * 100,
    getBorderColor,
    getProgressColor,
    getFieldSx
  };
}; 