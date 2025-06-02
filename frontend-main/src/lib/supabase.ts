import { createClient } from '@supabase/supabase-js';

// Supabaseの環境変数
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// 固定のストレージキー
export const AUTH_STORAGE_KEY = 'kagra-auth-token';

// 緊急クリーンアップ - 認証関連のストレージをすべて削除
export function cleanupAuthStorage() {
  try {
    const authKeys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (
        key.includes('supabase') || 
        key.includes('auth') || 
        key.includes('token') || 
        key.includes('session') ||
        key.includes('kagra')
      )) {
        authKeys.push(key);
      }
    }
    authKeys.forEach(key => localStorage.removeItem(key));
    return true;
  } catch (e) {
    console.error('ローカルストレージのクリアに失敗:', e);
    return false;
  }
}

// 環境変数チェック
if (!supabaseUrl || !supabaseKey) {
  console.error('Supabase環境変数が設定されていません。.envファイルを確認してください。');
}

// Supabaseクライアントの初期化
export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    storage: localStorage,
    storageKey: AUTH_STORAGE_KEY,
  }
});

// セッションをリセットする関数
export async function resetAuthSession() {
  try {
    // 現在のセッションをサインアウト
    await supabase.auth.signOut({ scope: 'global' });
    
    // ローカルストレージをクリア
    cleanupAuthStorage();
    
    return true;
  } catch (e) {
    console.error('認証セッションのリセットに失敗:', e);
    return false;
  }
}

// エラー監視
supabase.auth.onAuthStateChange((event) => {
  if (event === 'SIGNED_OUT') {
    console.log('サインアウト完了');
  } else if (event === 'SIGNED_IN') {
    console.log('サインイン完了');
  }
}); 