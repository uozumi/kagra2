"""
KAGRA API v1 ルーター設定

このファイルは、KAGRA API v1の全エンドポイントを統合し、
FastAPIルーターとして設定します。各機能領域のエンドポイントを
適切なプレフィックスとタグで整理し、APIドキュメントの生成を支援します。

ルーター構成:
- /auth: 認証・認可機能
- /users: ユーザー管理機能
- /admin: 管理機能
- /search: 検索機能
- /charaxy: Charaxyシステム機能
  - /charaxy/nodes: ノード管理
  - /charaxy: ブロック管理（レガシー互換性）
  - /charaxy/themes: テーマ管理
  - /charaxy/activity: アクティビティ追跡

設計原則:
- 明確なURL構造
- 機能別のタグ付け
- 競合回避のためのプレフィックス設計
- RESTful設計に準拠
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import users, auth, admin, search
from app.api.api_v1.endpoints import nodes, blocks, themes, activity

# メインAPIルーター作成
api_router = APIRouter(
    responses={
        404: {"description": "リソースが見つかりません"},
        500: {"description": "内部サーバーエラー"}
    }
)

# 認証関連エンドポイント
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"],
    responses={
        401: {"description": "認証が必要です"},
        403: {"description": "アクセス権限がありません"}
    }
)

# ユーザー関連エンドポイント
api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["users"],
    responses={
        401: {"description": "認証が必要です"},
        403: {"description": "アクセス権限がありません"}
    }
)

# 管理機能エンドポイント
api_router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["admin"],
    responses={
        401: {"description": "認証が必要です"},
        403: {"description": "管理者権限が必要です"}
    }
)

# 検索関連エンドポイント
api_router.include_router(
    search.router, 
    prefix="/search", 
    tags=["search"],
    responses={
        401: {"description": "認証が必要です"}
    }
)

# Charaxy関連エンドポイント - 具体的なプレフィックスで競合を回避
api_router.include_router(
    nodes.router, 
    prefix="/charaxy/nodes", 
    tags=["charaxy-nodes"],
    responses={
        401: {"description": "認証が必要です"},
        403: {"description": "アクセス権限がありません"}
    }
)

api_router.include_router(
    blocks.router, 
    prefix="/charaxy", 
    tags=["charaxy-blocks"],
    responses={
        401: {"description": "認証が必要です"},
        403: {"description": "アクセス権限がありません"}
    }
)

api_router.include_router(
    themes.router, 
    prefix="/charaxy/themes", 
    tags=["charaxy-themes"],
    responses={
        401: {"description": "認証が必要です"},
        403: {"description": "アクセス権限がありません"}
    }
)

api_router.include_router(
    activity.router, 
    prefix="/charaxy/activity", 
    tags=["charaxy-activity"],
    responses={
        401: {"description": "認証が必要です"}
    }
) 