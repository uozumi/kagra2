from enum import Enum
from typing import List, Dict, Set
from fastapi import HTTPException, Depends
import structlog
from functools import wraps

from app.core.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()

class Role(str, Enum):
    """ユーザーロール定義"""
    SUPER_ADMIN = "super_admin"      # システム全体の管理者
    TENANT_ADMIN = "tenant_admin"    # テナント管理者
    PROJECT_ADMIN = "project_admin"  # プロジェクト管理者
    EDITOR = "editor"                # 編集者
    VIEWER = "viewer"                # 閲覧者
    GUEST = "guest"                  # ゲスト

class Permission(str, Enum):
    """権限定義"""
    # システム管理
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_READ = "system:read"
    
    # テナント管理
    TENANT_CREATE = "tenant:create"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"
    TENANT_READ = "tenant:read"
    
    # ユーザー管理
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_READ = "user:read"
    
    # プロジェクト管理
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_READ = "project:read"
    
    # ノード管理
    NODE_CREATE = "node:create"
    NODE_UPDATE = "node:update"
    NODE_DELETE = "node:delete"
    NODE_READ = "node:read"
    
    # ブロック管理
    BLOCK_CREATE = "block:create"
    BLOCK_UPDATE = "block:update"
    BLOCK_DELETE = "block:delete"
    BLOCK_READ = "block:read"
    
    # テーマ管理
    THEME_CREATE = "theme:create"
    THEME_UPDATE = "theme:update"
    THEME_DELETE = "theme:delete"
    THEME_READ = "theme:read"

# ロールと権限のマッピング
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        Permission.SYSTEM_ADMIN,
        Permission.SYSTEM_READ,
        Permission.TENANT_CREATE,
        Permission.TENANT_UPDATE,
        Permission.TENANT_DELETE,
        Permission.TENANT_READ,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_READ,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_READ,
        Permission.NODE_CREATE,
        Permission.NODE_UPDATE,
        Permission.NODE_DELETE,
        Permission.NODE_READ,
        Permission.BLOCK_CREATE,
        Permission.BLOCK_UPDATE,
        Permission.BLOCK_DELETE,
        Permission.BLOCK_READ,
        Permission.THEME_CREATE,
        Permission.THEME_UPDATE,
        Permission.THEME_DELETE,
        Permission.THEME_READ,
    },
    Role.TENANT_ADMIN: {
        Permission.TENANT_READ,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_READ,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_READ,
        Permission.NODE_CREATE,
        Permission.NODE_UPDATE,
        Permission.NODE_DELETE,
        Permission.NODE_READ,
        Permission.BLOCK_CREATE,
        Permission.BLOCK_UPDATE,
        Permission.BLOCK_DELETE,
        Permission.BLOCK_READ,
        Permission.THEME_CREATE,
        Permission.THEME_UPDATE,
        Permission.THEME_DELETE,
        Permission.THEME_READ,
    },
    Role.PROJECT_ADMIN: {
        Permission.PROJECT_READ,
        Permission.NODE_CREATE,
        Permission.NODE_UPDATE,
        Permission.NODE_DELETE,
        Permission.NODE_READ,
        Permission.BLOCK_CREATE,
        Permission.BLOCK_UPDATE,
        Permission.BLOCK_DELETE,
        Permission.BLOCK_READ,
        Permission.THEME_CREATE,
        Permission.THEME_UPDATE,
        Permission.THEME_DELETE,
        Permission.THEME_READ,
    },
    Role.EDITOR: {
        Permission.PROJECT_READ,
        Permission.NODE_CREATE,
        Permission.NODE_UPDATE,
        Permission.NODE_DELETE,
        Permission.NODE_READ,
        Permission.BLOCK_CREATE,
        Permission.BLOCK_UPDATE,
        Permission.BLOCK_DELETE,
        Permission.BLOCK_READ,
        Permission.THEME_CREATE,
        Permission.THEME_UPDATE,
        Permission.THEME_READ,
    },
    Role.VIEWER: {
        Permission.PROJECT_READ,
        Permission.NODE_READ,
        Permission.BLOCK_READ,
        Permission.THEME_READ,
    },
    Role.GUEST: {
        Permission.BLOCK_READ,
        Permission.THEME_READ,
    }
}

class RBACService:
    """ロールベースアクセス制御サービス"""
    
    @staticmethod
    def get_user_permissions(user: User) -> Set[Permission]:
        """ユーザーの権限を取得"""
        user_role = Role(user.role) if hasattr(user, 'role') and user.role else Role.VIEWER
        return ROLE_PERMISSIONS.get(user_role, set())
    
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """ユーザーが特定の権限を持っているかチェック"""
        user_permissions = RBACService.get_user_permissions(user)
        return permission in user_permissions
    
    @staticmethod
    def check_permission(user: User, permission: Permission):
        """権限チェック（権限がない場合は例外を発生）"""
        user_permissions = RBACService.get_user_permissions(user)
        has_perm = permission in user_permissions
        
        logger.info("権限詳細チェック",
                   user_id=user.id,
                   user_role=getattr(user, 'role', 'unknown'),
                   required_permission=permission.value,
                   user_permissions=[p.value for p in user_permissions],
                   has_permission=has_perm)
        
        if not has_perm:
            logger.warning(
                "Permission denied",
                user_id=user.id,
                required_permission=permission.value,
                user_role=getattr(user, 'role', 'unknown'),
                user_permissions=[p.value for p in user_permissions]
            )
            raise HTTPException(
                status_code=403,
                detail=f"この操作には {permission.value} 権限が必要です"
            )
    
    @staticmethod
    def check_resource_ownership(user: User, resource_user_id: str, permission: Permission):
        """リソースの所有権チェック"""
        # 管理者権限がある場合はスキップ
        if RBACService.has_permission(user, Permission.SYSTEM_ADMIN):
            return
        
        # 自分のリソースでない場合は権限チェック
        if user.id != resource_user_id:
            RBACService.check_permission(user, permission)

# 権限チェック用のデコレータ関数
def require_permission(permission: Permission):
    """権限が必要なエンドポイント用のデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # FastAPIの依存性注入でcurrent_userを取得
            current_user = kwargs.get('current_user')
            
            if not current_user:
                # 引数からも確認（後方互換性のため）
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                logger.error("認証エラー: current_userが見つかりません", 
                           args_types=[type(arg).__name__ for arg in args],
                           kwargs_keys=list(kwargs.keys()))
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            try:
                # 権限チェック
                logger.info("権限チェック開始", 
                          user_id=current_user.id, 
                          user_role=getattr(current_user, 'role', 'unknown'),
                          required_permission=permission.value)
                
                RBACService.check_permission(current_user, permission)
                
                logger.info("権限チェック成功", 
                          user_id=current_user.id,
                          required_permission=permission.value)
                
            except Exception as e:
                logger.error("権限チェックエラー", 
                           user_id=getattr(current_user, 'id', 'unknown'),
                           required_permission=permission.value,
                           error=str(e))
                raise
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permissions(*permissions: Permission):
    """複数の権限が必要なエンドポイント用のデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_userを引数から取得
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            # kwargsからも確認
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            # 複数権限チェック
            for permission in permissions:
                RBACService.check_permission(current_user, permission)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# よく使用される権限チェック関数
def require_admin(func):
    """管理者権限が必要"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # current_userを引数から取得
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break
        
        # kwargsからも確認
        if not current_user:
            current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        RBACService.check_permission(current_user, Permission.SYSTEM_ADMIN)
        return await func(*args, **kwargs)
    return wrapper

def require_tenant_admin(func):
    """テナント管理者権限が必要"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # current_userを引数から取得
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break
        
        # kwargsからも確認
        if not current_user:
            current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        if not (RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN) or 
                RBACService.has_permission(current_user, Permission.TENANT_UPDATE)):
            raise HTTPException(status_code=403, detail="テナント管理者権限が必要です")
        return await func(*args, **kwargs)
    return wrapper

def require_project_admin(func):
    """プロジェクト管理者権限が必要"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # current_userを引数から取得
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break
        
        # kwargsからも確認
        if not current_user:
            current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        if not (RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN) or 
                RBACService.has_permission(current_user, Permission.TENANT_UPDATE) or
                RBACService.has_permission(current_user, Permission.PROJECT_UPDATE)):
            raise HTTPException(status_code=403, detail="プロジェクト管理者権限が必要です")
        return await func(*args, **kwargs)
    return wrapper

def require_editor(func):
    """編集者権限が必要"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # current_userを引数から取得
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break
        
        # kwargsからも確認
        if not current_user:
            current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        if not (RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN) or 
                RBACService.has_permission(current_user, Permission.TENANT_UPDATE) or
                RBACService.has_permission(current_user, Permission.PROJECT_UPDATE) or
                RBACService.has_permission(current_user, Permission.BLOCK_UPDATE)):
            raise HTTPException(status_code=403, detail="編集者権限が必要です")
        return await func(*args, **kwargs)
    return wrapper 