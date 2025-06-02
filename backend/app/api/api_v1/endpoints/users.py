from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.auth import get_current_user
from app.core.database import get_supabase_client
# 新システム
from app.core.rbac import require_database_permission, DatabaseRBACService
from app.models.user import User, UserUpdateRequest, UserUpdate, UserResponse
from app.services.charaxy_service import CharaxyService
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.core.audit import audit_log, AuditAction, log_user_action

logger = structlog.get_logger()
router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)


def get_charaxy_service(supabase = Depends(get_supabase_client)) -> CharaxyService:
    return CharaxyService(supabase)


def get_user_id_from_path(request: Request, **kwargs) -> str:
    """パスからユーザーIDを取得"""
    return kwargs.get('user_id') or request.path_params.get('user_id')


@router.get("/")
@limiter.limit("30/minute")
@require_database_permission("read")
async def get_users(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """ユーザー一覧取得（新データベースRBACシステム使用）"""
    return {"message": "Users endpoint"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("100/minute")
@audit_log(action=AuditAction.READ, resource_type="user")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """現在のユーザー情報取得"""
    try:
        logger.info("ユーザー情報取得", user_id=current_user.id)
        
        supabase = get_supabase_client()
        
        # user_profiles_viewから基本情報を取得
        avatar_url = None
        name = None
        try:
            profiles_view_response = supabase.table('user_profiles_view').select('name, avatar_url').eq('id', current_user.id).execute()
            if profiles_view_response.data and profiles_view_response.data[0]:
                view_data = profiles_view_response.data[0]
                name = view_data.get('name')
                avatar_url = view_data.get('avatar_url')
                logger.info("user_profiles_viewから基本情報取得成功", user_id=current_user.id)
        except Exception as e:
            logger.warning("user_profiles_viewからの基本情報取得エラー", user_id=current_user.id, error=str(e))
        
        # user_profilesテーブルから詳細情報を取得
        slack_member_id = None
        extension_number = None
        try:
            profiles_response = supabase.table('user_profiles').select('slack_member_id, extension_number, display_name, avatar_url').eq('user_id', current_user.id).execute()
            if profiles_response.data and profiles_response.data[0]:
                profile_data = profiles_response.data[0]
                slack_member_id = profile_data.get('slack_member_id')
                extension_number = profile_data.get('extension_number')
                # user_profiles_viewで取得できなかった場合のフォールバック
                if not avatar_url:
                    avatar_url = profile_data.get('avatar_url')
                logger.info("user_profilesから詳細情報取得成功", user_id=current_user.id)
        except Exception as e:
            logger.warning("user_profilesからの詳細情報取得エラー", user_id=current_user.id, error=str(e))
        
        # 所属情報を取得
        affiliations = []
        try:
            # user_affiliationsから所属情報を取得
            affiliations_response = supabase.table('user_affiliations').select('*').eq('user_id', current_user.id).execute()
            if affiliations_response.data:
                # テナントごとにグループ化
                tenant_groups = {}
                for aff in affiliations_response.data:
                    tenant_id = aff['tenant_id']
                    if tenant_id not in tenant_groups:
                        tenant_groups[tenant_id] = {
                            'tenantId': tenant_id,
                            'tenantName': aff['tenant_name'],
                            'departments': []
                        }
                    if aff.get('department_name'):
                        tenant_groups[tenant_id]['departments'].append(aff['department_name'])
                
                affiliations = list(tenant_groups.values())
                logger.info("所属情報取得成功", user_id=current_user.id, affiliations_count=len(affiliations))
            else:
                logger.info("所属情報が見つかりません", user_id=current_user.id)
                    
        except Exception as e:
            logger.warning("所属情報取得エラー", user_id=current_user.id, error=str(e))
        
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            role=current_user.role,
            avatar_url=avatar_url,
            name=name,
            slack_member_id=slack_member_id,
            extension_number=extension_number,
            affiliations=affiliations
        )
        
    except Exception as e:
        logger.error("ユーザー情報取得エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail="ユーザー情報の取得に失敗しました")


@router.put("/me", response_model=UserResponse)
@limiter.limit("10/minute")
@audit_log(action=AuditAction.USER_UPDATE, resource_type="user")
async def update_current_user(
    request: Request,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """現在のユーザー情報更新"""
    try:
        logger.info("ユーザー情報更新開始", user_id=current_user.id)
        
        supabase = get_supabase_client()
        
        # 更新データ準備
        update_data = {}
        if user_update.display_name is not None:
            update_data['display_name'] = user_update.display_name
        if user_update.email is not None:
            update_data['email'] = user_update.email
        
        if not update_data:
            raise HTTPException(status_code=400, detail="更新するデータがありません")
        
        # ユーザー情報更新
        response = supabase.table('user_profiles').update(update_data).eq('user_id', current_user.id).execute()
        
        if not response.data:
            raise Exception("データベースエラー: ユーザー情報の更新に失敗しました")
        
        updated_user = response.data[0]
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.USER_UPDATE,
            user=current_user,
            resource_type="user",
            resource_id=current_user.id,
            request=request,
            old_data={"display_name": current_user.display_name, "email": current_user.email},
            new_data=update_data
        )
        
        logger.info("ユーザー情報更新完了", user_id=current_user.id)
        
        return UserResponse(
            id=updated_user['user_id'],
            email=updated_user['email'],
            display_name=updated_user['display_name'],
            role=updated_user.get('role', 'user')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ユーザー情報更新エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail="ユーザー情報の更新に失敗しました")


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
@require_database_permission("read")
@audit_log(action=AuditAction.READ, resource_type="user", get_resource_id=get_user_id_from_path)
async def get_user(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """特定ユーザー情報取得（管理者権限必要）（新データベースRBACシステム使用）"""
    try:
        logger.info("新RBACシステムでユーザー情報取得開始", target_user_id=user_id, user_id=current_user.id)
        
        supabase = get_supabase_client()
        
        # ユーザー情報取得
        response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        user_data = response.data[0]
        
        logger.info("新RBACシステムでユーザー情報取得完了", target_user_id=user_id)
        
        return UserResponse(
            id=user_data['user_id'],
            email=user_data['email'],
            display_name=user_data['display_name'],
            role=user_data.get('role', 'user')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("新RBACシステムでユーザー情報取得エラー", target_user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="ユーザー情報の取得に失敗しました")


@router.get("/me/permissions")
async def get_current_user_permissions(
    current_user: User = Depends(get_current_user)
):
    """現在のユーザーの権限情報を取得"""
    supabase = get_supabase_client()
    
    try:
        # ユーザーの権限情報を取得
        permissions_response = supabase.table('user_permissions').select(
            'permission_name, resource_type, resource_id'
        ).eq('user_id', current_user.id).execute()
        
        permissions = permissions_response.data or []
        
        # 権限をグループ化
        grouped_permissions = {}
        for perm in permissions:
            resource_type = perm.get('resource_type', 'global')
            if resource_type not in grouped_permissions:
                grouped_permissions[resource_type] = []
            grouped_permissions[resource_type].append({
                'permission': perm['permission_name'],
                'resource_id': perm.get('resource_id')
            })
        
        return {
            'user_id': current_user.id,
            'permissions': grouped_permissions
        }
        
    except Exception as e:
        logger.error("権限情報取得エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail="権限情報の取得に失敗しました") 