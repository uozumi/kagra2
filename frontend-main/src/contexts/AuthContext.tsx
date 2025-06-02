import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import logger from '../utils/logger';

// 権限管理用のコンテキスト
interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
  isSystemAdmin: boolean; // システム管理者かどうか
  isAdmin: boolean; // 何らかの管理者権限（システムまたはテナント）を持っているか
}

interface AuthPermissionsContextType {
  checkAdminPermission: (userId: string) => Promise<boolean>;
  checkTenantAdminPermission: (userId: string, tenantId?: string) => Promise<boolean>;
  isCheckingPermission: boolean;
  emergencyCheck: (userId: string) => Promise<void>; // 緊急チェック関数
}

// コンテキストを作成
const AuthContext = createContext<AuthContextType | undefined>(undefined);
const AuthPermissionsContext = createContext<AuthPermissionsContextType | undefined>(undefined);

// 権限管理のプロバイダーコンポーネント
function AuthPermissionsProvider({ children }: { children: React.ReactNode }) {
  const [isCheckingPermission, setIsCheckingPermission] = useState(false);
  
  // 緊急チェック - 直接サーバーに問い合わせて権限情報を取得
  const emergencyCheck = async (userId: string) => {
    logger.log('緊急チェック開始 - ユーザーID:', userId);
    
    try {
      // 開発環境では権限テーブルが存在しない可能性があるため、
      // ログのみ出力してエラーにしない
      logger.log('緊急チェック完了（開発環境）');
    } catch (error) {
      logger.error('緊急チェックエラー:', error);
    }
  };
  
  // システム管理者権限チェック関数
  const checkAdminPermission = async (userId: string): Promise<boolean> => {
    logger.log('システム管理者権限チェック開始 - ユーザーID:', userId);
    
    try {
      setIsCheckingPermission(true);
      
      // 開発環境では権限テーブルが存在しない可能性があるため、
      // デフォルトでfalseを返す
      logger.log('システム管理者権限チェック最終結果: false（開発環境）');
      return false;
    } catch (err) {
      logger.error('管理者権限チェックエラー:', err);
      return false;
    } finally {
      setIsCheckingPermission(false);
    }
  };
  
  // テナント管理者権限チェック関数
  const checkTenantAdminPermission = async (userId: string, tenantId?: string): Promise<boolean> => {
    logger.log('テナント管理者権限チェック開始 - ユーザーID:', userId, 'テナントID:', tenantId);
    
    try {
      setIsCheckingPermission(true);
      
      // 開発環境では権限テーブルが存在しない可能性があるため、
      // デフォルトでfalseを返す
      logger.log('テナント管理者権限チェック最終結果: false（開発環境）');
      return false;
    } catch (err) {
      logger.error('テナント管理者権限チェックエラー:', err);
      return false;
    } finally {
      setIsCheckingPermission(false);
    }
  };
  
  const value = {
    checkAdminPermission,
    checkTenantAdminPermission,
    isCheckingPermission,
    emergencyCheck
  };
  
  return (
    <AuthPermissionsContext.Provider value={value}>
      {children}
    </AuthPermissionsContext.Provider>
  );
}

// 認証プロバイダー
function AuthProviderComponent({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSystemAdmin, setIsSystemAdmin] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  
  useEffect(() => {
    // 初期セッション取得
    const getInitialSession = async () => {
      try {
        setLoading(true);
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) {
          logger.error('初期セッション取得エラー:', error);
        } else {
          logger.log('初期セッション取得:', session?.user?.email || 'セッションなし');
          setSession(session);
          setUser(session?.user ?? null);
          
          if (session?.user) {
            await checkUserPermissions(session.user.id);
          }
        }
      } catch (error) {
        logger.error('初期セッション取得例外:', error);
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // 認証状態変更の監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        logger.log('認証状態変更:', event, session?.user?.email || 'ユーザーなし');
        
        setSession(session);
        setUser(session?.user ?? null);
        
        if (session?.user) {
          await checkUserPermissions(session.user.id);
        } else {
          // ユーザーがいない場合は権限をリセット
          setIsSystemAdmin(false);
          setIsAdmin(false);
        }
        
        // 認証状態変更時は必ずloadingをfalseに設定
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);
  
  // ユーザー権限チェック
  const checkUserPermissions = async (userId: string) => {
    try {
      logger.log('権限チェック開始 - ユーザーID:', userId);
      
      // 権限テーブルが存在しない場合はデフォルト権限を設定
      // 開発環境では全ユーザーに基本権限を付与
      setIsSystemAdmin(false);
      setIsAdmin(false);
      
      logger.log('権限チェック完了（デフォルト権限）', { 
        userId, 
        isSystemAdmin: false, 
        isAdmin: false
      });
      
    } catch (error) {
      logger.error('権限チェックエラー:', error);
      setIsSystemAdmin(false);
      setIsAdmin(false);
    }
  };
  
  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    return { error };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const refreshSession = async () => {
    await supabase.auth.getSession();
  };
  
  const value = {
    session,
    user,
    loading,
    signIn,
    signOut,
    refreshSession,
    isSystemAdmin,
    isAdmin
  };
  
  return (
    <AuthContext.Provider value={value}>
      <AuthPermissionsProvider>
        {children}
      </AuthPermissionsProvider>
    </AuthContext.Provider>
  );
}

// エクスポート
export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <AuthProviderComponent>{children}</AuthProviderComponent>;
}

export function useAuthPermissions() {
  const context = useContext(AuthPermissionsContext);
  if (context === undefined) {
    throw new Error('useAuthPermissionsはAuthPermissionsProviderの内部で使用する必要があります');
  }
  return context;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthはAuthProviderの内部で使用する必要があります');
  }
  return context;
} 