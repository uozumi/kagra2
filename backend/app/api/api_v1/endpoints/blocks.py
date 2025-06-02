from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.database import get_supabase_client
from app.core.auth import get_current_user
from app.core.security import query_sanitizer
from app.core.rbac import require_permission, Permission, RBACService
from app.core.audit import audit_log, AuditAction, log_user_action
from app.models.user import User
from app.models.charaxy import Block, BlockCreate, BlockUpdate, SetThemeRequest, BlockReorderRequest
from app.services.charaxy_service import CharaxyService

logger = structlog.get_logger()
router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

def get_charaxy_service(supabase = Depends(get_supabase_client)) -> CharaxyService:
    return CharaxyService(supabase)

def get_block_id_from_path(request: Request, **kwargs) -> str:
    """パスからブロックIDを取得"""
    return kwargs.get('block_id') or request.path_params.get('block_id')

@router.get("/nodes/{node_id}/blocks", response_model=List[Block])
@limiter.limit("30/minute")
@require_permission(Permission.BLOCK_READ)
@audit_log(action=AuditAction.READ, resource_type="block")
async def get_blocks(
    request: Request,
    node_id: str,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ノードのブロック一覧取得"""
    try:
        # UUIDバリデーション
        if not query_sanitizer.validate_uuid(node_id):
            raise HTTPException(status_code=400, detail="無効なノードIDです")
        
        logger.info("ブロック一覧取得開始", node_id=node_id, user_id=current_user.id)
        blocks = service.get_node_blocks(node_id)
        logger.info("ブロック一覧取得完了", node_id=node_id, count=len(blocks))
        return blocks
    except Exception as e:
        logger.error("ブロック一覧取得エラー", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック取得エラー: {str(e)}")

@router.get("/blocks/{block_id}")
@limiter.limit("60/minute")
@require_permission(Permission.BLOCK_READ)
@audit_log(action=AuditAction.READ, resource_type="block", get_resource_id=get_block_id_from_path)
async def get_block(
    request: Request,
    block_id: str,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """特定のブロック取得"""
    try:
        # UUIDバリデーション
        if not query_sanitizer.validate_uuid(block_id):
            raise HTTPException(status_code=400, detail="無効なブロックIDです")
        
        logger.info("ブロック詳細取得開始", block_id=block_id, user_id=current_user.id)
        block = service.get_block(block_id)
        
        if not block:
            logger.warning("ブロックが見つかりません", block_id=block_id)
            raise HTTPException(status_code=404, detail="ブロックが見つかりません")
        
        # 所有者チェック（user_idフィールドを使用）
        if block.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このブロックにアクセスする権限がありません")
        
        logger.info("ブロック詳細取得完了", block_id=block_id)
        return block
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ブロック詳細取得エラー", block_id=block_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック取得エラー: {str(e)}")

@router.post("/blocks", response_model=Block)
@limiter.limit("5/minute")
@require_permission(Permission.BLOCK_CREATE)
@audit_log(action=AuditAction.BLOCK_CREATE, resource_type="block")
async def create_block(
    request: Request,
    block: BlockCreate,
    current_user: User = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """ブロック作成"""
    try:
        # 入力値のサニタイズ
        block.title = query_sanitizer.sanitize_string(block.title)
        if block.content:
            block.content = query_sanitizer.sanitize_string(block.content)
        
        # UUIDバリデーション
        if not query_sanitizer.validate_uuid(block.node_id):
            raise HTTPException(status_code=400, detail="無効なノードIDです")
        
        logger.info("ブロック作成開始", node_id=block.node_id, user_id=current_user.id, title=block.title)
        
        # ソート順を取得
        sort_response = supabase.table('blocks').select('sort_order').eq('node_id', block.node_id).is_('deleted_at', 'null').order('sort_order', desc=True).limit(1).execute()
        next_sort_order = (sort_response.data[0]['sort_order'] + 1) if sort_response.data else 0
        
        block_data = {
            **block.dict(),
            "user_id": current_user.id,
            "sort_order": next_sort_order
        }
        
        response = supabase.table('blocks').insert(block_data).execute()
        
        # Supabaseの新しいクライアントではresponse.errorは存在しない
        if not response.data:
            logger.error("ブロック作成DBエラー", error="No data returned from insert")
            raise Exception("データベースエラー: ブロックの作成に失敗しました")
        
        created_block = response.data[0]
        logger.info("ブロック作成完了", block_id=created_block['id'])
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.BLOCK_CREATE,
            user=current_user,
            resource_type="block",
            resource_id=created_block['id'],
            request=request,
            new_data={"title": block.title, "content": block.content}
        )
        
        return created_block
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ブロック作成エラー", node_id=block.node_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック作成エラー: {str(e)}")

@router.put("/blocks/{block_id}", response_model=Block)
@limiter.limit("10/minute")
@require_permission(Permission.BLOCK_UPDATE)
@audit_log(action=AuditAction.BLOCK_UPDATE, resource_type="block", get_resource_id=get_block_id_from_path)
async def update_block(
    request: Request,
    block_id: str,
    block: BlockUpdate,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service),
    supabase = Depends(get_supabase_client)
):
    """ブロック更新"""
    try:
        logger.info("ブロック更新開始", block_id=block_id, user_id=current_user.id)
        
        # 既存ブロック取得
        existing_block = service.get_block_by_id(block_id)
        if not existing_block:
            raise HTTPException(status_code=404, detail="ブロックが見つかりません")
        
        # 所有者チェック
        if existing_block.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このブロックを更新する権限がありません")
        
        # ブロック更新
        updated_block = service.update_block(block_id, block.dict(exclude_unset=True))
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.BLOCK_UPDATE,
            user=current_user,
            resource_type="block",
            resource_id=block_id,
            request=request,
            old_data={"title": existing_block.get('title'), "content": existing_block.get('content')},
            new_data=block.dict(exclude_unset=True)
        )
        
        logger.info("ブロック更新完了", block_id=block_id)
        return updated_block
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ブロック更新エラー", block_id=block_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック更新エラー: {str(e)}")

@router.delete("/blocks/{block_id}")
@limiter.limit("5/minute")
@require_permission(Permission.BLOCK_DELETE)
@audit_log(action=AuditAction.BLOCK_DELETE, resource_type="block", get_resource_id=get_block_id_from_path)
async def delete_block(
    request: Request,
    block_id: str,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service),
    supabase = Depends(get_supabase_client)
):
    """ブロック削除"""
    try:
        logger.info("ブロック削除開始", block_id=block_id, user_id=current_user.id)
        
        # 既存ブロック取得
        existing_block = service.get_block_by_id(block_id)
        if not existing_block:
            raise HTTPException(status_code=404, detail="ブロックが見つかりません")
        
        # 所有者チェック
        if existing_block.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このブロックを削除する権限がありません")
        
        # ブロック削除（論理削除）
        service.delete_block(block_id)
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.BLOCK_DELETE,
            user=current_user,
            resource_type="block",
            resource_id=block_id,
            request=request,
            old_data={"title": existing_block.get('title'), "content": existing_block.get('content')}
        )
        
        logger.info("ブロック削除完了", block_id=block_id)
        return {"message": "ブロックが削除されました"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ブロック削除エラー", block_id=block_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック削除エラー: {str(e)}")

@router.put("/blocks/reorder")
@limiter.limit("10/minute")
@require_permission(Permission.BLOCK_UPDATE)
@audit_log(action=AuditAction.BLOCK_REORDER, resource_type="block", get_resource_id=get_block_id_from_path)
async def reorder_blocks(
    request: Request,
    reorder_request: BlockReorderRequest,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ブロック順序変更"""
    try:
        logger.info("ブロック順序変更開始", user_id=current_user.id, block_count=len(reorder_request.block_ids))
        
        # 並び替え実行
        service.reorder_blocks(reorder_request.block_ids, current_user.id)
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.BLOCK_REORDER,
            user=current_user,
            resource_type="block",
            resource_id="multiple",
            request=request,
            new_data={"block_ids": reorder_request.block_ids}
        )
        
        logger.info("ブロック順序変更完了", user_id=current_user.id)
        return {"message": "ブロック順序が更新されました"}
    except Exception as e:
        logger.error("ブロック順序変更エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ブロック順序更新エラー: {str(e)}")

@router.put("/blocks/{block_id}/theme")
@limiter.limit("15/minute")
@require_permission(Permission.BLOCK_UPDATE)
@audit_log(action=AuditAction.BLOCK_UPDATE, resource_type="block", get_resource_id=get_block_id_from_path)
async def set_block_theme(
    request: Request,
    block_id: str,
    theme_data: dict,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service),
    supabase = Depends(get_supabase_client)
):
    """ブロックのテーマ設定"""
    try:
        logger.info("ブロックテーマ設定開始", block_id=block_id, user_id=current_user.id)
        
        # 既存ブロック取得
        existing_block = service.get_block_by_id(block_id)
        if not existing_block:
            raise HTTPException(status_code=404, detail="ブロックが見つかりません")
        
        # 所有者チェック
        if existing_block.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このブロックを更新する権限がありません")
        
        theme_id = theme_data.get('theme_id')
        response = supabase.table('blocks').update({"block_theme_id": theme_id}).eq('id', block_id).execute()
        
        # Supabaseの新しいクライアントではresponse.errorは存在しない
        if not response.data:
            logger.error("ブロックテーマ設定DBエラー", block_id=block_id, error="No data returned from update")
            raise Exception("データベースエラー: テーマの設定に失敗しました")
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.BLOCK_UPDATE,
            user=current_user,
            resource_type="block",
            resource_id=block_id,
            request=request,
            old_data={"theme_id": existing_block.get('block_theme_id')},
            new_data={"theme_id": theme_id}
        )
        
        logger.info("ブロックテーマ設定完了", block_id=block_id, theme_id=theme_id)
        return {"message": "テーマが設定されました"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ブロックテーマ設定エラー", block_id=block_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"テーマ設定エラー: {str(e)}") 