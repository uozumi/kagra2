from typing import Optional, List, Dict, Any
from fastapi import HTTPException, Depends
import structlog
from functools import wraps

from app.core.auth import get_current_user
from app.core.database import get_supabase_client
from app.models.user import User

logger = structlog.get_logger()

class DatabaseRBACService:
    """データベースベースの権限管理サービス"""
    
    @staticmethod
    def get_user_permissions(user_id: str, supabase) -> List[Dict[str, Any]]:
        """ユーザーの全権限を取得"""
        try:
            response = supabase.table('user_permissions_view').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error("権限取得エラー", user_id=user_id, error=str(e))
            return []
    
    @staticmethod
    def is_system_admin(user_id: str, supabase) -> bool:
        """システム管理者権限チェック"""
        try:
            response = supabase.table('user_permissions_view').select('*').eq('user_id', user_id).eq('is_system_admin', True).execute()
            return bool(response.data)
        except Exception as e:
            logger.error("システム管理者権限チェックエラー", user_id=user_id, error=str(e))
            return False
    
    @staticmethod
    def is_tenant_admin(user_id: str, tenant_id: str, supabase) -> bool:
        """テナント管理者権限チェック"""
        try:
            response = supabase.table('user_permissions_view').select('*').eq('user_id', user_id).eq('tenant_id', tenant_id).eq('permission_type', 'tenant').execute()
            return bool(response.data)
        except Exception as e:
            logger.error("テナント管理者権限チェックエラー", user_id=user_id, tenant_id=tenant_id, error=str(e))
            return False
    
    @staticmethod
    def get_user_tenant_permissions(user_id: str, supabase) -> List[str]:
        """ユーザーが管理者権限を持つテナントIDのリストを取得"""
        try:
            response = supabase.table('user_permissions_view').select('tenant_id').eq('user_id', user_id).eq('permission_type', 'tenant').execute()
            return [item['tenant_id'] for item in response.data or [] if item['tenant_id']]
        except Exception as e:
            logger.error("テナント権限取得エラー", user_id=user_id, error=str(e))
            return []
    
    @staticmethod
    def check_permission(user: User, permission_type: str, tenant_id: Optional[str] = None) -> None:
        """権限チェック（権限がない場合は例外を発生）"""
        supabase = get_supabase_client()
        
        logger.info("データベース権限チェック開始",
                   user_id=user.id,
                   permission_type=permission_type,
                   tenant_id=tenant_id)
        
        # システム管理者は全権限を持つ
        if DatabaseRBACService.is_system_admin(user.id, supabase):
            logger.info("システム管理者権限で許可", user_id=user.id)
            return
        
        # テナント権限チェック
        if permission_type == "tenant" and tenant_id:
            if DatabaseRBACService.is_tenant_admin(user.id, tenant_id, supabase):
                logger.info("テナント管理者権限で許可", user_id=user.id, tenant_id=tenant_id)
                return
        
        # 一般的な読み取り権限（認証済みユーザー）
        if permission_type in ["read", "view"]:
            logger.info("読み取り権限で許可", user_id=user.id)
            return
        
        # 権限なし
        logger.warning("権限拒否",
                      user_id=user.id,
                      permission_type=permission_type,
                      tenant_id=tenant_id)
        raise HTTPException(
            status_code=403,
            detail=f"この操作には {permission_type} 権限が必要です"
        )

def require_database_permission(permission_type: str, tenant_id: Optional[str] = None):
    """データベースベースの権限チェックデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_userを取得
            current_user = kwargs.get('current_user')
            
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                logger.error("認証エラー: current_userが見つかりません")
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            try:
                DatabaseRBACService.check_permission(current_user, permission_type, tenant_id)
                logger.info("データベース権限チェック成功", 
                          user_id=current_user.id,
                          permission_type=permission_type)
                
            except Exception as e:
                logger.error("データベース権限チェックエラー", 
                           user_id=getattr(current_user, 'id', 'unknown'),
                           permission_type=permission_type,
                           error=str(e))
                raise
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_system_admin(func):
    """システム管理者権限が必要"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        if not current_user:
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
        
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        supabase = get_supabase_client()
        if not DatabaseRBACService.is_system_admin(current_user.id, supabase):
            raise HTTPException(status_code=403, detail="システム管理者権限が必要です")
        
        return await func(*args, **kwargs)
    return wrapper

def require_tenant_admin(tenant_id: str):
    """テナント管理者権限が必要"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            supabase = get_supabase_client()
            
            # システム管理者またはテナント管理者
            if (DatabaseRBACService.is_system_admin(current_user.id, supabase) or 
                DatabaseRBACService.is_tenant_admin(current_user.id, tenant_id, supabase)):
                return await func(*args, **kwargs)
            
            raise HTTPException(status_code=403, detail="テナント管理者権限が必要です")
        return wrapper
    return decorator 