from typing import Optional, Dict, Any
import structlog

from app.core.database import get_supabase_client
from app.models.user import UserCreate

logger = structlog.get_logger()


class AuthService:
    """認証サービス"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_user(self, user_data: UserCreate) -> Optional[Dict[str, Any]]:
        """新規ユーザー作成"""
        try:
            result = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password
            })
            return result
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            return None
    
    async def sign_in(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """ユーザーログイン"""
        try:
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return result
        except Exception as e:
            logger.error("Failed to sign in", error=str(e))
            return None
    
    async def sign_out(self, access_token: str) -> bool:
        """ユーザーログアウト"""
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            logger.error("Failed to sign out", error=str(e))
            return False
    
    async def get_current_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """現在のユーザー情報取得"""
        try:
            result = self.supabase.auth.get_user(access_token)
            return result.user if result else None
        except Exception as e:
            logger.error("Failed to get current user", error=str(e))
            return None
    
    async def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """セッションリフレッシュ"""
        try:
            result = self.supabase.auth.refresh_session(refresh_token)
            return result
        except Exception as e:
            logger.error("Failed to refresh session", error=str(e))
            return None 