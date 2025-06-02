"""
KAGRA API Application Package

KAGRAシステムのバックエンドAPIアプリケーション。
FastAPIを使用したRESTful APIサーバーを提供します。

主な機能:
- Charaxyシステム（ノード・ブロック管理）
- ユーザー認証・認可
- テーマ管理
- アクティビティ追跡
- セキュリティ機能（レート制限、SQLインジェクション対策など）
"""

__version__ = "2.0.0"
__title__ = "KAGRA API"
__description__ = "KAGRA システムのバックエンドAPI"
__author__ = "KAGRA Development Team"

# アプリケーション情報
APP_INFO = {
    "title": __title__,
    "description": __description__,
    "version": __version__,
    "features": {
        "rate_limiting": True,
        "security_headers": True,
        "rbac": True,
        "audit_logging": True,
        "advanced_sql_injection_protection": True,
        "brute_force_protection": True,
        "ip_filtering": True
    }
} 