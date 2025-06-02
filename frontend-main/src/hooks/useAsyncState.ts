import { useState } from 'react';

export interface UseAsyncStateReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (asyncFn: () => Promise<T>) => Promise<T>;
  setData: (data: T | null) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

/**
 * 非同期処理の状態管理を共通化するカスタムフック
 * loading, error, dataの状態を統一的に管理
 */
export const useAsyncState = <T>(initialLoading: boolean = false): UseAsyncStateReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(initialLoading);
  const [error, setError] = useState<string | null>(null);
  
  const execute = async (asyncFn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      const result = await asyncFn();
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'エラーが発生しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const reset = () => {
    setData(null);
    setLoading(initialLoading);
    setError(null);
  };
  
  return { 
    data, 
    loading, 
    error, 
    execute, 
    setData, 
    setError, 
    setLoading,
    reset 
  };
}; 