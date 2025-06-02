import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

/**
 * ユーザーのアバターURLをFastAPI経由で取得するカスタムフック
 */
export const useUserAvatar = (userId: string | undefined) => {
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchAvatar = async () => {
      if (!userId) {
        setAvatarUrl(null);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        // Supabaseセッションからアクセストークンを取得
        const { data: { session } } = await supabase.auth.getSession();
        
        // FastAPI経由でユーザー情報を取得
        const response = await fetch(`/api/v1/users/${userId}`, {
          headers: {
            'Authorization': `Bearer ${session?.access_token || ''}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          if (response.status === 404) {
            setAvatarUrl(null);
            return;
          }
          throw new Error(`ユーザー情報取得エラー: ${response.status}`);
        }
        
        const userData = await response.json();
        setAvatarUrl(userData.avatar_url || null);
        
      } catch (err) {
        console.error('アバター取得エラー:', err);
        setError(err instanceof Error ? err : new Error('アバター取得エラー'));
        setAvatarUrl(null);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAvatar();
  }, [userId]);

  return { avatarUrl, loading, error };
}; 