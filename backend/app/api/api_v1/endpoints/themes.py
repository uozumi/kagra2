from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.auth import get_current_user
from app.core.database import get_supabase_client
# 新システム
from app.core.rbac import require_database_permission, DatabaseRBACService
from app.core.audit import audit_log, AuditAction, log_user_action
from app.models.user import User
from app.models.theme import ThemeCreate, ThemeUpdate, ThemeResponse
from app.models.charaxy import Block  # 正しいインポート
from app.services.charaxy_service import CharaxyService
import structlog

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
@require_database_permission("read")
@audit_log(action=AuditAction.READ, resource_type="theme")
async def get_themes(
    request: Request,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """テーマ一覧取得（新データベースRBACシステム使用）"""
    try:
        logger.info("新RBACシステムでテーマ一覧取得開始", user_id=current_user.id)
        
        supabase = get_supabase_client()
        
        # ユーザーが作成したテーマのみ取得
        response = supabase.table('block_themes').select('*').eq('creator_id', current_user.id).range(skip, skip + limit - 1).execute()
        
        if not response.data:
            return []
        
        themes = []
        for theme_data in response.data:
            # 各テーマのブロック数を計算
            blocks_response = supabase.table('blocks').select('id').eq('block_theme_id', theme_data['id']).is_('deleted_at', 'null').execute()
            block_count = len(blocks_response.data) if blocks_response.data else 0
            
            theme = ThemeResponse(
                id=theme_data['id'],
                title=theme_data['title'],
                description=None,  # descriptionは常にNone
                created_by=theme_data['creator_id'],
                created_at=theme_data['created_at'],
                updated_at=theme_data['updated_at'],
                block_count=block_count
            )
            themes.append(theme)
        
        logger.info("新RBACシステムでテーマ一覧取得完了", user_id=current_user.id, count=len(themes))
        return themes
        
    except Exception as e:
        logger.error("新RBACシステムでテーマ一覧取得エラー", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="テーマ一覧の取得に失敗しました")

@router.get("/{theme_id}", response_model=ThemeResponse)
@limiter.limit("60/minute")
@require_database_permission("read")
@audit_log(action=AuditAction.READ, resource_type="theme", get_resource_id=get_theme_id_from_path)
async def get_theme(
    request: Request,
    theme_id: str,
    current_user: User = Depends(get_current_user)
):
    """テーマ詳細取得"""
    try:
        logger.info(f"[DEBUG] テーマ詳細取得開始 - テーマID: {theme_id}, ユーザーID: {current_user.id}")
        
        supabase = get_supabase_client()
        
        # テーマ取得
        response = supabase.table('block_themes').select('*').eq('id', theme_id).execute()
        
        if not response.data:
            logger.warning(f"[DEBUG] テーマが見つかりません - テーマID: {theme_id}")
            raise HTTPException(status_code=404, detail="テーマが見つかりません")
        
        theme_data = response.data[0]
        logger.info(f"[DEBUG] テーマデータ取得成功 - 作成者: {theme_data.get('creator_id')}, 現在ユーザー: {current_user.id}")
        
        # 所有者チェックを完全に削除（誰でもアクセス可能）
        
        return ThemeResponse(
            id=theme_data['id'],
            title=theme_data['title'],
            description=None,  # descriptionは常にNone
            created_by=theme_data.get('creator_id'),  # NULLの場合に備えてgetを使用
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
@require_database_permission("read")
async def get_theme_blocks(
    request: Request,
    theme_id: str,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """テーマ別ブロック取得"""
    try:
        logger.info(f"[DEBUG] テーマブロック一覧取得開始 - テーマID: {theme_id}, ユーザーID: {current_user.id}")
        blocks = service.get_theme_blocks_filtered(theme_id, current_user.id)
        logger.info(f"[DEBUG] テーマブロック一覧取得完了 - テーマID: {theme_id}, ブロック数: {len(blocks)}")
        return blocks
    except Exception as e:
        logger.error(f"[DEBUG] テーマブロック一覧取得エラー - テーマID: {theme_id}, エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ブロック取得エラー: {str(e)}")

@router.post("/", response_model=ThemeResponse)
@limiter.limit("5/minute")
@require_database_permission("create")
@audit_log(action=AuditAction.THEME_CREATE, resource_type="theme")
async def create_theme(
    request: Request,
    theme: ThemeCreate,
    current_user: User = Depends(get_current_user)
):
    """新しいテーマを作成"""
    try:
        logger.info("テーマ作成開始", user_id=current_user.id, title=theme.title)
        
        supabase = get_supabase_client()
        
        # テーマデータ準備（descriptionフィールドを削除）
        theme_data = {
            "title": theme.title,
            "creator_id": current_user.id
        }
        
        logger.info("テーマデータ準備完了", theme_data=theme_data)
        
        # テーマ作成
        response = supabase.table('block_themes').insert(theme_data).execute()
        
        logger.info("Supabaseレスポンス", response_data=response.data, response_error=getattr(response, 'error', None))
        
        if not response.data:
            logger.error("テーマ作成失敗: レスポンスデータなし", response=response.__dict__)
            raise Exception("データベースエラー: データの作成に失敗しました")
        
        created_theme = response.data[0]
        
        # 詳細な監査ログを記録（descriptionを削除）
        log_user_action(
            action=AuditAction.THEME_CREATE,
            user=current_user,
            resource_type="theme",
            resource_id=created_theme['id'],
            request=request,
            new_data={"title": theme.title}
        )
        
        logger.info("テーマ作成完了", theme_id=created_theme['id'])
        
        return ThemeResponse(
            id=created_theme['id'],
            title=created_theme['title'],
            description=None,  # descriptionは常にNone
            created_by=created_theme['creator_id'],
            created_at=created_theme['created_at'],
            updated_at=created_theme['updated_at']
        )
        
    except Exception as e:
        logger.error("テーマ作成エラー詳細", error=str(e), user_id=current_user.id, error_type=type(e).__name__)
        import traceback
        logger.error("テーマ作成エラートレースバック", traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail="テーマの作成に失敗しました")

@router.put("/{theme_id}", response_model=ThemeResponse)
@limiter.limit("10/minute")
@require_database_permission("update")
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
        
        # 更新データ準備（titleのみ）
        update_data = {}
        if theme_update.title is not None:
            update_data['title'] = theme_update.title
        
        if not update_data:
            raise HTTPException(status_code=400, detail="更新するデータがありません")
        
        # テーマ更新
        response = supabase.table('block_themes').update(update_data).eq('id', theme_id).execute()
        
        if not response.data:
            raise Exception("データベースエラー: データの更新に失敗しました")
        
        updated_theme = response.data[0]
        
        # 詳細な監査ログを記録（descriptionを削除）
        log_user_action(
            action=AuditAction.THEME_UPDATE,
            user=current_user,
            resource_type="theme",
            resource_id=theme_id,
            request=request,
            old_data={"title": existing_theme['title']},
            new_data=update_data
        )
        
        return ThemeResponse(
            id=updated_theme['id'],
            title=updated_theme['title'],
            description=None,  # descriptionは常にNone
            created_by=updated_theme['creator_id'],
            created_at=updated_theme['created_at'],
            updated_at=updated_theme['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update theme", error=str(e), theme_id=theme_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="テーマの更新に失敗しました") 