from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_supabase_client
from app.core.auth import get_current_user
from app.core.rbac import require_permission, Permission, RBACService
from app.core.audit import audit_log, AuditAction, log_user_action
from app.models.user import User
from app.models.charaxy import Node, NodeCreate, NodeUpdate
from app.services.charaxy_service import CharaxyService

logger = structlog.get_logger()
router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

def get_charaxy_service(supabase = Depends(get_supabase_client)) -> CharaxyService:
    return CharaxyService(supabase)


def get_node_id_from_path(request: Request, **kwargs) -> str:
    """パスからノードIDを取得"""
    return kwargs.get('node_id') or request.path_params.get('node_id')


@router.get("/", response_model=List[Node])
async def get_nodes(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service),
    skip: int = 0,
    limit: int = 100
):
    """ノード一覧取得"""
    try:
        logger.info("ノード一覧取得開始", user_id=current_user.id, skip=skip, limit=limit)
        
        nodes = service.get_nodes_filtered(current_user.id, skip, limit)
        
        logger.info("ノード一覧取得完了", user_id=current_user.id, count=len(nodes))
        
        return nodes
    except Exception as e:
        logger.error("ノード一覧取得エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ノード取得エラー: {str(e)}")


@router.get("/{node_id}", response_model=Node)
@audit_log(action=AuditAction.READ, resource_type="node", get_resource_id=get_node_id_from_path)
@limiter.limit("60/minute")
@require_permission(Permission.NODE_READ)
async def get_node(
    request: Request,
    node_id: str,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ノード詳細取得"""
    try:
        logger.info("ノード詳細取得開始", node_id=node_id, user_id=current_user.id)
        
        # ユーザー情報付きでノードを取得
        node = service.get_node_with_user_info(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail="ノードが見つかりません")
        
        # 所有者チェック（公開ノードまたは自分のノード）
        if not node.get('is_public', False) and node.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このノードにアクセスする権限がありません")
        
        logger.info("ノード詳細取得完了", node_id=node_id)
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ノード詳細取得エラー", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ノード取得エラー: {str(e)}")


@router.post("/", response_model=Node)
@audit_log(action=AuditAction.NODE_CREATE, resource_type="node")
@limiter.limit("5/minute")
@require_permission(Permission.NODE_CREATE)
async def create_node(
    request: Request,
    node: NodeCreate,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ノード作成"""
    try:
        logger.info("ノード作成開始", user_id=current_user.id, title=node.title)
        
        # ノードデータ準備
        node_data = {
            **node.dict(),
            "user_id": current_user.id
        }
        
        created_node = service.create_node(node_data)
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.NODE_CREATE,
            user=current_user,
            resource_type="node",
            resource_id=created_node['id'],
            request=request,
            new_data={"title": node.title, "description": node.description}
        )
        
        logger.info("ノード作成完了", node_id=created_node['id'])
        return created_node
    except Exception as e:
        logger.error("ノード作成エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ノード作成エラー: {str(e)}")


@router.put("/{node_id}", response_model=Node)
@audit_log(action=AuditAction.NODE_UPDATE, resource_type="node", get_resource_id=get_node_id_from_path)
@limiter.limit("10/minute")
@require_permission(Permission.NODE_UPDATE)
async def update_node(
    request: Request,
    node_id: str,
    node_update: NodeUpdate,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ノード更新"""
    try:
        logger.info("ノード更新開始", node_id=node_id, user_id=current_user.id)
        
        # 既存ノード取得
        existing_node = service.get_node_by_id(node_id)
        if not existing_node:
            raise HTTPException(status_code=404, detail="ノードが見つかりません")
        
        # 所有者チェック
        if existing_node.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このノードを更新する権限がありません")
        
        # ノード更新
        updated_node = service.update_node(node_id, node_update.dict(exclude_unset=True))
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.NODE_UPDATE,
            user=current_user,
            resource_type="node",
            resource_id=node_id,
            request=request,
            old_data={"title": existing_node.get('title'), "description": existing_node.get('description')},
            new_data=node_update.dict(exclude_unset=True)
        )
        
        logger.info("ノード更新完了", node_id=node_id)
        return updated_node
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ノード更新エラー", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ノード更新エラー: {str(e)}")


@router.delete("/{node_id}")
@audit_log(action=AuditAction.NODE_DELETE, resource_type="node", get_resource_id=get_node_id_from_path)
@limiter.limit("5/minute")
@require_permission(Permission.NODE_DELETE)
async def delete_node(
    request: Request,
    node_id: str,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ノード削除"""
    try:
        logger.info("ノード削除開始", node_id=node_id, user_id=current_user.id)
        
        # 既存ノード取得
        existing_node = service.get_node_by_id(node_id)
        if not existing_node:
            raise HTTPException(status_code=404, detail="ノードが見つかりません")
        
        # 所有者チェック
        if existing_node.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="このノードを削除する権限がありません")
        
        # ノード削除（論理削除）
        service.delete_node(node_id)
        
        # 詳細な監査ログを記録
        log_user_action(
            action=AuditAction.NODE_DELETE,
            user=current_user,
            resource_type="node",
            resource_id=node_id,
            request=request,
            old_data={"title": existing_node.get('title'), "description": existing_node.get('description')}
        )
        
        logger.info("ノード削除完了", node_id=node_id)
        return {"message": "ノードが削除されました"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ノード削除エラー", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ノード削除エラー: {str(e)}") 