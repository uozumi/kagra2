from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from app.core.config import settings
from app.core.database import get_supabase_client
from app.models.user import User

logger = structlog.get_logger()

# HTTPベアラー認証
security = HTTPBearer()


class AuthService:
    """認証サービス"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """アクセストークンを作成"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="トークンの作成に失敗しました"
            )
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """リフレッシュトークンを作成"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="リフレッシュトークンの作成に失敗しました"
            )
    
    @staticmethod
    def verify_supabase_token(token: str) -> Dict[str, Any]:
        """Supabaseトークンを検証してユーザー情報を返す"""
        try:
            supabase = get_supabase_client()
            # Supabaseの認証APIを使用してトークンを検証
            user_response = supabase.auth.get_user(token)
            
            if not user_response.user:
                logger.warning("Supabase token verification failed: no user")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="無効なトークンです",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Supabaseのユーザー情報からペイロードを構築
            return {
                "sub": user_response.user.id,
                "email": user_response.user.email,
                "aud": "authenticated"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Supabase token verification error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="トークンの検証に失敗しました",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """トークンを検証してペイロードを返す（Supabase優先）"""
        # まずSupabaseトークンとして検証を試行
        try:
            return AuthService.verify_supabase_token(token)
        except HTTPException as supabase_error:
            logger.info("Supabase token verification failed, trying JWT", error=str(supabase_error.detail))
            
            # Supabaseで失敗した場合、従来のJWT検証を試行
            try:
                secret_key = settings.SUPABASE_JWT_SECRET or settings.JWT_SECRET_KEY
                payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
                return payload
            except jwt.ExpiredSignatureError:
                logger.warning("Token expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="トークンの有効期限が切れています",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except InvalidTokenError as e:
                logger.warning("Invalid token", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="無効なトークンです",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        """トークンからユーザー情報を取得"""
        try:
            payload = AuthService.verify_token(token)
            user_id = payload.get("sub")
            
            if user_id is None:
                logger.warning("Token missing user ID")
                return None
            
            # データベースからユーザー情報を取得
            supabase = get_supabase_client()
            result = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not result.data:
                logger.warning("User not found", user_id=user_id)
                return None
            
            user_data = result.data[0]
            return User(**user_data)
            
        except HTTPException:
            # 既にHTTPExceptionの場合はそのまま再発生
            raise
        except Exception as e:
            logger.error("Failed to get user from token", error=str(e))
            return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """現在のユーザーを取得"""
    token = credentials.credentials
    
    user = AuthService.get_user_from_token(token)
    if user is None:
        logger.warning("Authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info("User authenticated", user_id=user.id, email=user.email)
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """現在のユーザーを取得（オプショナル）"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証"""
    import bcrypt
    
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化"""
    import bcrypt
    
    try:
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error("Password hashing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="パスワードの処理に失敗しました"
        )


def authenticate_user(email: str, password: str) -> Optional[User]:
    """ユーザーを認証"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("*").eq("email", email).execute()
        
        if not result.data:
            logger.warning("User not found for authentication", email=email)
            return None
        
        user_data = result.data[0]
        user = User(**user_data)
        
        # パスワード検証（Supabaseの認証を使用している場合は、この部分は不要かもしれません）
        if hasattr(user, 'password_hash') and user.password_hash:
            if not verify_password(password, user.password_hash):
                logger.warning("Password verification failed", email=email)
                return None
        
        logger.info("User authenticated successfully", user_id=user.id, email=email)
        return user
        
    except Exception as e:
        logger.error("Authentication error", email=email, error=str(e))
        return None


def create_user_tokens(user: User) -> Dict[str, str]:
    """ユーザーのアクセストークンとリフレッシュトークンを作成"""
    access_token = AuthService.create_access_token(data={"sub": user.id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    } 