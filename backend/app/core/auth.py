from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional
import httpx
import json
from functools import lru_cache
import logging

from app.core.config import settings
from app.core.database import get_supabase_client
from app.models.user import User

security = HTTPBearer()

logger = logging.getLogger(__name__)

@lru_cache()
def get_supabase_jwt_secret():
    """Supabase JWT秘密鍵を取得"""
    return settings.SUPABASE_JWT_SECRET

async def verify_supabase_token(token: str) -> dict:
    """Supabase JWTトークンを検証"""
    try:
        # Supabase REST APIを使用してトークンを検証
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": settings.SUPABASE_ANON_KEY
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers=headers
            )
            
            if response.status_code != 200:
                response_text = response.text
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"無効なトークンです: {response.status_code} - {response_text}"
                )
            
            user_data = response.json()
            return user_data
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"認証サービスへの接続エラー: {str(e)}"
        )
    except Exception as e:
        logger.error("認証エラー", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """現在のユーザーを取得"""
    try:
        # トークンを検証してユーザー情報を取得
        user_data = await verify_supabase_token(credentials.credentials)
        
        # user_profilesテーブルからdisplay_nameとroleを取得
        supabase = get_supabase_client()
        profile_response = supabase.table('user_profiles').select('display_name').eq('user_id', user_data["id"]).execute()
        
        display_name = None
        role = "editor"  # デフォルト値（一般ユーザーは編集権限を持つ）
        
        if profile_response.data and len(profile_response.data) > 0:
            profile = profile_response.data[0]
            display_name = profile.get('display_name')
        
        # Userモデルに変換
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            display_name=display_name,
            role=role,
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at"),
            email_confirmed_at=user_data.get("email_confirmed_at"),
            last_sign_in_at=user_data.get("last_sign_in_at"),
            raw_app_meta_data=user_data.get("app_metadata", {}),
            raw_user_meta_data=user_data.get("user_metadata", {}),
            is_anonymous=user_data.get("is_anonymous", False)
        )
        
        return user
        
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error("get_current_user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"ユーザー情報の取得に失敗しました: {str(e)}"
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """現在のユーザーを取得（オプショナル）"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None 