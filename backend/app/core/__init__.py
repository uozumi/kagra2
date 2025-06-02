"""
Core Package - アプリケーションの基盤機能

このパッケージには、KAGRAアプリケーションの基盤となる機能が含まれています。
セキュリティ、認証、データベース、ログ、設定管理などの横断的関心事を提供します。

主要コンポーネント:
- config: アプリケーション設定管理
- database: データベース接続とクエリ機能
- auth: 認証・認可機能
- security: セキュリティ機能（SQLインジェクション対策、レート制限など）
- rbac: ロールベースアクセス制御
- audit: 監査ログ機能
- redis: Redisキャッシュ機能
- logging: 構造化ログ機能
"""

# パッケージメタデータ
__package_name__ = "core"
__description__ = "KAGRA API基盤機能パッケージ"

# 主要コンポーネントのインポート（必要に応じて）
from .config import settings
from .database import get_supabase_client

__all__ = [
    "settings",
    "get_supabase_client"
] 