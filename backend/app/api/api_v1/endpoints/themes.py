from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.database import get_supabase_client
from app.core.auth import get_current_user
from app.core.rbac import require_permission, Permission, RBACService
from app.core.audit import audit_log, AuditAction, log_user_action
from app.models.user import User
from app.models.charaxy import BlockTheme, BlockThemeCreate, Block
from app.models.theme import ThemeCreate, ThemeUpdate, ThemeResponse
from app.services.charaxy_service import CharaxyService

logger = structlog.get_logger()
router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

def get_charaxy_service(supabase = Depends(get_supabase_client)) -> CharaxyService:
    return CharaxyService(supabase)

def get_theme_id_from_path(request: Request, **kwargs) -> str:
    """パスからテーマIDを取得"""
    return kwargs.get('theme_id') or request.path_params.get('theme_id')

@router.get("/", response_model=List[ThemeResponse])
@limiter.limit("30/minute")
@require_permission(Permission.THEME_READ)
@audit_log(action=AuditAction.READ, resource_type="theme")
async def get_themes(
    request: Request,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """テーマ一覧取得"""
    try:
        supabase = get_supabase_client()
        
        # ユーザーが作成したテーマのみ取得
        response = supabase.table('block_themes').select('*').eq('creator_id', current_user.id).range(skip, skip + limit - 1).execute()
        
        if not response.data:
            return []
        
        themes = []
        for theme_data in response.data:
            theme = ThemeResponse(
                id=theme_data['id'],
                title=theme_data['title'],
                description=theme_data.get('description'),
                created_by=theme_data['creator_id'],
                created_at=theme_data['created_at'],
                updated_at=theme_data['updated_at']
            )
            themes.append(theme)
        
        return themes
        
    except Exception as e:
        logger.error("Failed to get themes", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="テーマ一覧の取得に失敗しました")

@router.get("/{theme_id}", response_model=ThemeResponse)
@limiter.limit("60/minute")
@require_permission(Permission.THEME_READ)
@audit_log(action=AuditAction.READ, resource_type="theme", get_resource_id=get_theme_id_from_path)
async def get_theme(
    request: Request,
    theme_id: str,
    current_user: User = Depends(get_current_user)
):
    """テーマ詳細取得"""
    try:
        supabase = get_supabase_client()
        
        # テーマ取得
        response = supabase.table('block_themes').select('*').eq('id', theme_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="テーマが見つかりません")
        
        theme_data = response.data[0]
        
        # 所有者チェック
        if theme_data['creator_id'] != current_user.id:
            raise HTTPException(status_code=403, detail="このテーマにアクセスする権限がありません")
        
        return ThemeResponse(
            id=theme_data['id'],
            title=theme_data['title'],
            description=theme_data.get('description'),
            created_by=theme_data['creator_id'],
            created_at=theme_data['created_at'],
            updated_at=theme_data['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get theme", error=str(e), theme_id=theme_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="テーマの取得に失敗しました")

@router.get("/{theme_id}/blocks", response_model=List[Block])
@limiter.limit("30/minute")
async def get_theme_blocks(
    request: Request,
    theme_id: str,
    current_user: User = Depends(require_permission(Permission.BLOCK_READ)),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """テーマ別ブロック取得"""
    try:
        logger.info("テーマブロック一覧取得開始", theme_id=theme_id, user_id=current_user.id)
        blocks = service.get_theme_blocks_filtered(theme_id, current_user.id)
        logger.info("テーマブロック一覧取得完了", theme_id=theme_id, count=len(blocks))
        return blocks
    except Exception as e:
        logger.error("テーマブロック一覧取得エラー", theme_id=theme_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック取得エラー: {str(e)}")

@router.post("/", response_model=ThemeResponse)
@limiter.limit("5/minute")
@require_permission(Permission.THEME_CREATE)
@audit_log(action=AuditAction.THEME_CREATE, resource_type="theme")
async def create_theme(
    request: Request,
    theme: ThemeCreate,
    current_user: User = Depends(get_current_user)
):
    """新しいテーマを作成"""
    try:
        supabase = get_supabase_client()
        
        # テーマデータ準備
        theme_data = {
            "title": theme.title,
            "description": theme.description,
            "creator_id": current_user.id
        }
        
        # テーマ作成
        response = supabase.table('block_themes').insert(theme_data).execute()
        
        if not response.data:
            raise Exception("データベースエラー: データの作成に失敗しました")
        
        created_theme = response.data[0]
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.THEME_CREATE,
            user=current_user,
            resource_type="theme",
            resource_id=created_theme['id'],
            request=request,
            new_data={"title": theme.title, "description": theme.description}
        )
        
        return ThemeResponse(
            id=created_theme['id'],
            title=created_theme['title'],
            description=created_theme.get('description'),
            created_by=created_theme['creator_id'],
            created_at=created_theme['created_at'],
            updated_at=created_theme['updated_at']
        )
        
    except Exception as e:
        logger.error("Failed to create theme", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="テーマの作成に失敗しました")

@router.put("/{theme_id}", response_model=ThemeResponse)
@limiter.limit("10/minute")
@require_permission(Permission.THEME_UPDATE)
@audit_log(action=AuditAction.THEME_UPDATE, resource_type="theme", get_resource_id=get_theme_id_from_path)
async def update_theme(
    request: Request,
    theme_id: str,
    theme_update: ThemeUpdate,
    current_user: User = Depends(get_current_user)
):
    """テーマを更新"""
    try:
        supabase = get_supabase_client()
        
        # 既存テーマ取得
        existing_response = supabase.table('block_themes').select('*').eq('id', theme_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="テーマが見つかりません")
        
        existing_theme = existing_response.data[0]
        
        # 所有者チェック
        if existing_theme['creator_id'] != current_user.id:
            raise HTTPException(status_code=403, detail="このテーマを更新する権限がありません")
        
        # 更新データ準備
        update_data = {}
        if theme_update.title is not None:
            update_data['title'] = theme_update.title
        if theme_update.description is not None:
            update_data['description'] = theme_update.description
        
        if not update_data:
            raise HTTPException(status_code=400, detail="更新するデータがありません")
        
        # テーマ更新
        response = supabase.table('block_themes').update(update_data).eq('id', theme_id).execute()
        
        if not response.data:
            raise Exception("データベースエラー: データの更新に失敗しました")
        
        updated_theme = response.data[0]
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.THEME_UPDATE,
            user=current_user,
            resource_type="theme",
            resource_id=theme_id,
            request=request,
            old_data={"title": existing_theme['title'], "description": existing_theme.get('description')},
            new_data=update_data
        )
        
        return ThemeResponse(
            id=updated_theme['id'],
            title=updated_theme['title'],
            description=updated_theme.get('description'),
            created_by=updated_theme['creator_id'],
            created_at=updated_theme['created_at'],
            updated_at=updated_theme['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update theme", error=str(e), theme_id=theme_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="テーマの更新に失敗しました") 