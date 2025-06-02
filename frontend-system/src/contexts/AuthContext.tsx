import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import { apiClient } from '../lib/api';
import logger from '../utils/logger';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isSystemAdmin: boolean;
  signOut: () => Promise<void>;
  checkSystemAdminPermission: (userId: string, existingSession?: Session | null) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSystemAdmin, setIsSystemAdmin] = useState(false);

  // デバッグ用：loading状態の変化をログ出力
  const setLoadingWithLog = (newLoading: boolean, reason: string) => {
    logger.log(`🔄 Loading状態変更: ${loading} -> ${newLoading} (理由: ${reason})`);
    setLoading(newLoading);
  };

  // FastAPI経由でシステム管理者権限チェック
  const checkSystemAdminPermission = async (userId: string, existingSession?: Session | null): Promise<boolean> => {
    try {
      logger.log('🔐 FastAPI経由でシステム管理者権限チェック開始 - ユーザーID:', userId);
      
      let currentSession = existingSession;
      
      // 既存のセッションがない場合のみSupabaseから取得
      if (!currentSession) {
        logger.log('📡 Supabaseセッション取得を開始...');
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          logger.error('❌ セッション取得エラー:', error);
          return false;
        }
        
        currentSession = session;
      } else {
        logger.log('✅ 既存のセッション情報を使用');
      }
      
      logger.log('🎫 現在のセッション情報:', {
        hasSession: !!currentSession,
        hasAccessToken: !!currentSession?.access_token,
        userId: currentSession?.user?.id,
        tokenLength: currentSession?.access_token?.length
      });
      
      if (!currentSession?.access_token) {
        logger.error('❌ アクセストークンがありません');
        return false;
      }
      
      logger.log('🚀 APIリクエスト開始:', `/api/v1/admin/system/users/${userId}/permissions`);
      const response = await apiClient.get(`/api/v1/admin/system/users/${userId}/permissions`);
      const hasPermission = response?.is_system_admin === true;
      
      logger.log('✅ FastAPI権限チェック結果:', {
        response,
        hasPermission
      });
      return hasPermission;
      
    } catch (error) {
      logger.error('❌ FastAPI権限チェックエラー:', error);
      logger.error('❌ FastAPIサーバーが起動していない可能性があります。');
      logger.error('❌ または認証トークンが無効です。');
      return false;
    }
  };

  // ユーザー権限チェック
  const checkUserPermissions = async (userId: string) => {
    try {
      logger.log('🔍 権限チェック開始 - ユーザーID:', userId);
      
      // タイムアウト付きで権限チェックを実行
      const timeoutPromise = new Promise<boolean>((_, reject) => {
        setTimeout(() => reject(new Error('権限チェック全体がタイムアウトしました')), 15000); // 15秒でタイムアウト
      });
      
      const permissionPromise = checkSystemAdminPermission(userId);
      
      const hasSystemAdminPermission = await Promise.race([permissionPromise, timeoutPromise]);
      setIsSystemAdmin(hasSystemAdminPermission);
      
      logger.log('✅ 権限チェック完了', { 
        userId, 
        isSystemAdmin: hasSystemAdminPermission
      });
      return hasSystemAdminPermission;
    } catch (error) {
      logger.error('❌ 権限チェック中にエラーが発生:', error);
      setIsSystemAdmin(false);
      return false;
    }
  };

  // 認証状態の変更を監視
  useEffect(() => {
    logger.log('🚀 AuthProvider useEffect開始');
    
    // 初期セッション取得
    const getInitialSession = async () => {
      logger.log('📡 初期セッション取得開始');
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          setUser(session.user);
          setSession(session);
          logger.log('👤 初期セッション - ユーザーあり:', session.user.id);
          
          // 権限チェック（既存のセッション情報を渡す）
          const hasPermission = await checkSystemAdminPermission(session.user.id, session);
          setIsSystemAdmin(hasPermission);
          logger.log('🔐 初期権限チェック結果:', hasPermission);
        } else {
          logger.log('👤 初期セッション - ユーザーなし');
        }
      } catch (error) {
        logger.error('❌ 初期セッション取得エラー:', error);
      } finally {
        // 必ずローディングを終了
        setLoading(false);
        logger.log('🔄 Loading状態変更: true -> false (理由: 初期セッション取得完了)');
      }
    };

    // 認証状態変更の監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      logger.log('🔄 認証状態変更:', event, session?.user?.id);
      
      // INITIAL_SESSIONイベントは初期セッション取得で処理済みなのでスキップ
      if (event === 'INITIAL_SESSION') {
        logger.log('⏭️ INITIAL_SESSIONイベントはスキップ（重複処理を防ぐ）');
        return;
      }
      
      setLoading(true);
      logger.log('🔄 Loading状態変更: false -> true (理由: 認証状態変更:', event + ')');
      
      try {
        if (session?.user) {
          setUser(session.user);
          setSession(session);
          logger.log('👤 認証状態変更 - ユーザーあり:', session.user.id);
          
          // 権限チェック（既存のセッション情報を渡す）
          logger.log('🔍 権限チェック開始 - ユーザーID:', session.user.id);
          const hasPermission = await checkSystemAdminPermission(session.user.id, session);
          setIsSystemAdmin(hasPermission);
          logger.log('🔐 権限チェック結果:', hasPermission);
        } else {
          setUser(null);
          setSession(null);
          setIsSystemAdmin(false);
          logger.log('👤 認証状態変更 - ユーザーなし');
        }
      } catch (error) {
        logger.error('❌ 認証状態変更処理エラー:', error);
        // エラーが発生した場合は権限なしとして扱う
        setIsSystemAdmin(false);
      } finally {
        // 必ずローディングを終了
        setLoading(false);
        logger.log('🔄 Loading状態変更: true -> false (理由: 認証状態変更処理完了)');
      }
    });

    getInitialSession();

    return () => {
      logger.log('🧹 AuthProvider cleanup');
      subscription.unsubscribe();
    };
  }, []);

  // サインアウト
  const signOut = async () => {
    try {
      logger.log('🚪 サインアウト開始');
      const { error } = await supabase.auth.signOut();
      if (error) {
        logger.error('❌ サインアウトエラー:', error);
      } else {
        setUser(null);
        setSession(null);
        setIsSystemAdmin(false);
        logger.log('✅ サインアウト完了');
      }
    } catch (error) {
      logger.error('❌ サインアウト例外:', error);
    }
  };

  // デバッグ用：現在の状態をログ出力
  useEffect(() => {
    logger.log('📊 AuthContext状態:', {
      loading,
      hasUser: !!user,
      hasSession: !!session,
      isSystemAdmin,
      userId: user?.id
    });
  }, [loading, user, session, isSystemAdmin]);

  const value = {
    user,
    session,
    loading,
    isSystemAdmin,
    signOut,
    checkSystemAdminPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    console.error('❌ useAuth must be used within an AuthProvider');
    console.error('❌ 現在のコンポーネントツリー:', new Error().stack);
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};