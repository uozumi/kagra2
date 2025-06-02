from fastapi import APIRouter

from app.api.api_v1.endpoints import users, auth, admin, search
from app.api.api_v1.endpoints import nodes, blocks, themes, activity

api_router = APIRouter()

# 認証関連
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# ユーザー関連
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 管理機能
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# 検索関連
api_router.include_router(search.router, prefix="/search", tags=["search"])

# Charaxy関連エンドポイント - 具体的なプレフィックスで競合を回避
api_router.include_router(nodes.router, prefix="/charaxy/nodes", tags=["charaxy-nodes"])
api_router.include_router(blocks.router, prefix="/charaxy", tags=["charaxy-blocks"])
api_router.include_router(themes.router, prefix="/charaxy/themes", tags=["charaxy-themes"])
api_router.include_router(activity.router, prefix="/charaxy/activity", tags=["charaxy-activity"]) 