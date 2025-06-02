from fastapi import APIRouter, Request, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.rbac import require_permission, Permission
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

@router.get("/")
@limiter.limit("30/minute")
@require_permission(Permission.BLOCK_READ)
async def search(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """検索機能"""
    return {"message": "Search endpoint"} 