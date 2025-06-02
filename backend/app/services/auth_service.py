"""
認証サービス

Supabase Authを使用したユーザー認証機能を提供します。
ユーザー登録、ログイン、ログアウト、セッション管理などの操作を行います。
"""

from typing import Optional, Dict, Any
import structlog

from app.core.database import get_supabase_client
from app.models.user import UserCreate

logger = structlog.get_logger()


class AuthService:
    """認証サービスクラス
    
    Supabase Authを使用した認証機能を提供します。
    """
    
    def __init__(self):
        """認証サービスを初期化"""
        self.supabase = get_supabase_client()
    
    async def create_user(self, user_data: UserCreate) -> Optional[Dict[str, Any]]:
        """新規ユーザー作成
        
        Args:
            user_data: ユーザー作成データ
            
        Returns:
            作成されたユーザー情報、失敗時はNone
        """
        try:
            logger.info("ユーザー作成開始", email=user_data.email)
            
            result = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "display_name": user_data.display_name
                    }
                }
            })
            
            if result.user:
                logger.info("ユーザー作成成功", user_id=result.user.id, email=user_data.email)
            else:
                logger.warning("ユーザー作成失敗: ユーザーオブジェクトなし", email=user_data.email)
                
            return result.model_dump() if result else None
            
        except Exception as e:
            logger.error("ユーザー作成エラー", email=user_data.email, error=str(e))
            return None
    
    async def sign_in(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """ユーザーログイン
        
        Args:
            email: メールアドレス
            password: パスワード
            
        Returns:
            認証結果、失敗時はNone
        """
        try:
            logger.info("ログイン試行開始", email=email)
            
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result.user:
                logger.info("ログイン成功", user_id=result.user.id, email=email)
            else:
                logger.warning("ログイン失敗: ユーザーオブジェクトなし", email=email)
                
            return result.model_dump() if result else None
            
        except Exception as e:
            logger.error("ログインエラー", email=email, error=str(e))
            return None
    
    async def sign_out(self, access_token: Optional[str] = None) -> bool:
        """ユーザーログアウト
        
        Args:
            access_token: アクセストークン（未使用、後方互換性のため残存）
            
        Returns:
            ログアウト成功時True、失敗時False
        """
        try:
            logger.info("ログアウト開始")
            
            self.supabase.auth.sign_out()
            
            logger.info("ログアウト成功")
            return True
            
        except Exception as e:
            logger.error("ログアウトエラー", error=str(e))
            return False
    
    async def get_current_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """現在のユーザー情報取得
        
        Args:
            access_token: アクセストークン
            
        Returns:
            ユーザー情報、失敗時はNone
        """
        try:
            logger.debug("現在ユーザー情報取得開始")
            
            result = self.supabase.auth.get_user(access_token)
            
            if result and result.user:
                logger.debug("現在ユーザー情報取得成功", user_id=result.user.id)
                return result.user.model_dump()
            else:
                logger.warning("現在ユーザー情報取得失敗: ユーザーオブジェクトなし")
                return None
                
        except Exception as e:
            logger.error("現在ユーザー情報取得エラー", error=str(e))
            return None
    
    async def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """セッションリフレッシュ
        
        Args:
            refresh_token: リフレッシュトークン
            
        Returns:
            新しいセッション情報、失敗時はNone
        """
        try:
            logger.info("セッションリフレッシュ開始")
            
            result = self.supabase.auth.refresh_session(refresh_token)
            
            if result and result.session:
                logger.info("セッションリフレッシュ成功", user_id=result.user.id if result.user else None)
                return result.model_dump()
            else:
                logger.warning("セッションリフレッシュ失敗: セッションオブジェクトなし")
                return None
                
        except Exception as e:
            logger.error("セッションリフレッシュエラー", error=str(e))
            return None 