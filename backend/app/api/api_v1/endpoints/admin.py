from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Dict, Any
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.database import get_supabase_client
from app.core.auth import get_current_user
from app.core.rbac import require_permission, Permission, require_admin
from app.models.user import User
from app.core.audit import audit_log, AuditAction, log_user_action

logger = structlog.get_logger()
router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

@router.get("/")
@limiter.limit("20/minute")
async def admin(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """管理機能"""
    return {"message": "Admin endpoint"}


def get_user_id_from_path(request: Request, **kwargs) -> str:
    """パスからユーザーIDを取得"""
    return kwargs.get('user_id') or request.path_params.get('user_id')


@router.get("/system/users")
@limiter.limit("20/minute")
@require_admin
@audit_log(action=AuditAction.READ, resource_type="admin_user_list")
async def get_system_users(
    request: Request,
    current_user: User = Depends(require_admin),
    supabase = Depends(get_supabase_client)
):
    """全ユーザー取得（システム管理者のみ）"""
    try:
        # 全ユーザーの取得
        users_response = supabase.table('users').select('id, email, name, created_at').order('created_at', desc=True).execute()
        
        # システム管理者権限を持つユーザーの取得
        admin_permissions_response = supabase.table('user_system_permissions').select('user_id').eq('permission_level', 1).execute()
        
        admin_user_ids = set()
        if admin_permissions_response.data:
            admin_user_ids = {perm['user_id'] for perm in admin_permissions_response.data}
        
        # ユーザーデータと権限情報をマージ
        users_with_permissions = []
        for user in users_response.data or []:
            users_with_permissions.append({
                **user,
                'is_system_admin': user['id'] in admin_user_ids
            })
        
        return users_with_permissions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("全ユーザー取得エラー", error=str(e))
        raise HTTPException(status_code=500, detail="ユーザー情報の取得中にエラーが発生しました")


@router.get("/system/users/{user_id}/permissions")
@limiter.limit("10/minute")
@require_admin
@audit_log(action=AuditAction.READ, resource_type="admin_user_permissions", get_resource_id=get_user_id_from_path)
async def get_user_permissions(
    request: Request,
    user_id: str,
    current_user: User = Depends(require_admin),
    supabase = Depends(get_supabase_client)
):
    """ユーザーの権限情報を取得"""
    try:
        # システム管理者権限チェック
        admin_response = supabase.table('user_system_permissions').select('*').eq('user_id', user_id).eq('permission_level', 1).execute()
        
        is_system_admin = bool(admin_response.data and len(admin_response.data) > 0)
        
        return {
            "user_id": user_id,
            "is_system_admin": is_system_admin,
            "permissions": {
                "system_admin": is_system_admin
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ユーザー権限取得エラー", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="権限情報の取得中にエラーが発生しました")


@router.post("/system/users/{user_id}/admin")
@limiter.limit("5/minute")
@require_admin
@audit_log(action=AuditAction.USER_ROLE_CHANGE, resource_type="admin_user_permissions", get_resource_id=get_user_id_from_path)
async def grant_admin_permission(
    request: Request,
    user_id: str,
    current_user: User = Depends(require_admin),
    supabase = Depends(get_supabase_client)
):
    """システム管理者権限を付与"""
    try:
        # 既に権限があるかチェック
        existing_response = supabase.table('user_system_permissions').select('*').eq('user_id', user_id).eq('permission_level', 1).execute()
        
        if existing_response.data and len(existing_response.data) > 0:
            return {"message": "既にシステム管理者権限を持っています"}
        
        # 権限を付与
        insert_response = supabase.table('user_system_permissions').insert({
            'user_id': user_id,
            'permission_level': 1,
            'granted_by': current_user.id
        }).execute()
        
        return {"message": "システム管理者権限を付与しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("権限付与エラー", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="権限付与中にエラーが発生しました")


@router.delete("/system/users/{user_id}/admin")
@limiter.limit("5/minute")
async def revoke_admin_permission(
    request: Request,
    user_id: str,
    current_user: User = Depends(require_admin),
    supabase = Depends(get_supabase_client)
):
    """システム管理者権限を削除"""
    try:
        # 自分自身の権限は削除できない
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="自分自身の権限は削除できません")
        
        # 権限を削除
        delete_response = supabase.table('user_system_permissions').delete().eq('user_id', user_id).eq('permission_level', 1).execute()
        
        return {"message": "システム管理者権限を削除しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("権限削除エラー", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="権限削除中にエラーが発生しました")


async def check_system_admin_permission(user_id: str, supabase) -> bool:
    """システム管理者権限チェック"""
    try:
        response = supabase.table('user_system_permissions').select('*').eq('user_id', user_id).eq('permission_level', 1).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        logger.error("権限チェックエラー", user_id=user_id, error=str(e))
        return False 