from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.database import db_service
from app.core.redis import cache_set, cache_get, cache_delete
from app.core.audit import audit_log, AuditAction, log_authentication_attempt
from app.services.auth_service import AuthService
from app.models.user import UserResponse, UserCreate, UserLogin

logger = structlog.get_logger()
router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
@audit_log(action=AuditAction.USER_CREATE, resource_type="user")
async def register(request: Request, user_data: UserCreate):
    """新規ユーザー登録"""
    try:
        # メールアドレスの重複チェック
        existing_user = db_service.get_user_by_email(user_data.email)
        if existing_user:
            # 登録失敗をログ記録
            log_authentication_attempt(
                success=False,
                email=user_data.email,
                request=request,
                failure_reason="メールアドレス重複"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に登録されています"
            )
        
        # Supabase Authでユーザー作成
        auth_result = await auth_service.create_user(user_data)
        
        if not auth_result:
            # 登録失敗をログ記録
            log_authentication_attempt(
                success=False,
                email=user_data.email,
                request=request,
                failure_reason="Supabase Auth登録失敗"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ユーザー登録に失敗しました"
            )
        
        # ユーザープロファイル作成
        profile_data = {
            "user_id": auth_result["user"]["id"],
            "email": user_data.email,
            "display_name": user_data.display_name,
            "role": "user"
        }
        
        profile = db_service.create_user_profile(profile_data)
        if not profile:
            logger.error("Failed to create user profile", user_id=auth_result["user"]["id"])
        
        # レスポンス作成
        user_response = UserResponse(
            id=auth_result["user"]["id"],
            email=user_data.email,
            display_name=user_data.display_name,
            role="user"
        )
        
        # 登録成功をログ記録
        log_authentication_attempt(
            success=True,
            user=user_response,
            request=request
        )
        
        return TokenResponse(
            access_token=auth_result["session"]["access_token"],
            expires_in=auth_result["session"]["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        # 登録失敗をログ記録
        log_authentication_attempt(
            success=False,
            email=user_data.email,
            request=request,
            failure_reason=f"システムエラー: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー登録中にエラーが発生しました"
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
@audit_log(action=AuditAction.LOGIN, resource_type="authentication")
async def login(request: Request, credentials: UserLogin):
    """ユーザーログイン"""
    try:
        # Supabase Authでログイン
        auth_result = await auth_service.sign_in(credentials.email, credentials.password)
        
        if not auth_result:
            # ログイン失敗をログ記録
            log_authentication_attempt(
                success=False,
                email=credentials.email,
                request=request,
                failure_reason="認証情報が正しくありません"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="メールアドレスまたはパスワードが正しくありません"
            )
        
        # ユーザー情報取得
        user_data = db_service.get_user_by_id(auth_result["user"]["id"])
        if not user_data:
            # ログイン失敗をログ記録
            log_authentication_attempt(
                success=False,
                email=credentials.email,
                request=request,
                failure_reason="ユーザー情報が見つかりません"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザー情報が見つかりません"
            )
        
        # セッション情報をキャッシュ
        session_key = f"session:{auth_result['user']['id']}"
        await cache_set(session_key, {
            "user_id": auth_result["user"]["id"],
            "email": user_data["email"],
            "role": user_data.get("role", "user")
        }, ttl=3600)  # 1時間
        
        user_response = UserResponse(
            id=auth_result["user"]["id"],
            email=user_data["email"],
            display_name=user_data.get("display_name", ""),
            role=user_data.get("role", "user")
        )
        
        # ログイン成功をログ記録
        log_authentication_attempt(
            success=True,
            user=user_response,
            request=request
        )
        
        return TokenResponse(
            access_token=auth_result["session"]["access_token"],
            expires_in=auth_result["session"]["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        # ログイン失敗をログ記録
        log_authentication_attempt(
            success=False,
            email=credentials.email,
            request=request,
            failure_reason=f"システムエラー: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン中にエラーが発生しました"
        )


@router.post("/logout")
@limiter.limit("10/minute")
@audit_log(action=AuditAction.LOGOUT, resource_type="authentication")
async def logout(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """ユーザーログアウト"""
    try:
        # トークンからユーザーID取得
        user_data = await auth_service.get_current_user(credentials.credentials)
        if user_data:
            # セッションキャッシュを削除
            session_key = f"session:{user_data['id']}"
            await cache_delete(session_key)
        
        # Supabase Authでログアウト
        await auth_service.sign_out(credentials.credentials)
        
        return {"message": "ログアウトしました"}
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログアウト中にエラーが発生しました"
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
@audit_log(action=AuditAction.LOGIN, resource_type="authentication")
async def refresh_token(request: Request, refresh_request: RefreshTokenRequest):
    """トークンリフレッシュ"""
    try:
        # リフレッシュトークンで新しいアクセストークンを取得
        auth_result = await auth_service.refresh_session(refresh_request.refresh_token)
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なリフレッシュトークンです"
            )
        
        # ユーザー情報取得
        user_data = db_service.get_user_by_id(auth_result["user"]["id"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザー情報が見つかりません"
            )
        
        user_response = UserResponse(
            id=auth_result["user"]["id"],
            email=user_data["email"],
            display_name=user_data.get("display_name", ""),
            role=user_data.get("role", "user")
        )
        
        return TokenResponse(
            access_token=auth_result["session"]["access_token"],
            expires_in=auth_result["session"]["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="トークンリフレッシュ中にエラーが発生しました"
        )


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")
@audit_log(action=AuditAction.READ, resource_type="user")
async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """現在のユーザー情報取得"""
    try:
        # トークンからユーザー情報取得
        user_data = await auth_service.get_current_user(credentials.credentials)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです"
            )
        
        # データベースから最新のユーザー情報取得
        db_user = db_service.get_user_by_id(user_data["id"])
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザー情報が見つかりません"
            )
        
        return UserResponse(
            id=user_data["id"],
            email=db_user["email"],
            display_name=db_user.get("display_name", ""),
            role=db_user.get("role", "user")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get current user failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー情報取得中にエラーが発生しました"
        ) 