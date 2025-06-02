from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.database import get_supabase_client
from app.core.auth import get_current_user
from app.core.rbac import require_permission, Permission
from app.models.user import User
from app.models.charaxy import ActivityItem
from app.services.charaxy_service import CharaxyService
from app.core.audit import audit_log, AuditAction

logger = structlog.get_logger()
router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

def get_charaxy_service(supabase = Depends(get_supabase_client)) -> CharaxyService:
    return CharaxyService(supabase)

@router.get("/", response_model=List[ActivityItem])
@limiter.limit("20/minute")
@audit_log(action=AuditAction.READ, resource_type="activity")
async def get_activity(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: CharaxyService = Depends(get_charaxy_service)
):
    """ユーザーアクティビティ取得"""
    try:
        logger.info("アクティビティ取得開始", user_id=current_user.id)
        activities = service.get_user_activity(current_user.id)
        logger.info("アクティビティ取得完了", user_id=current_user.id, count=len(activities))
        return activities
    except Exception as e:
        logger.error("アクティビティ取得エラー", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=f"アクティビティ取得エラー: {str(e)}") 