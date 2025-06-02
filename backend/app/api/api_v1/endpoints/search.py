from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
# 新システム
from app.core.rbac import require_database_permission
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

@router.get("/")
@limiter.limit("30/minute")
@require_database_permission("read")
async def search(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """検索機能（新データベースRBACシステム使用）"""
    return {"message": "Search endpoint"} 