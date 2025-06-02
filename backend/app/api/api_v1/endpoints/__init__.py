"""
Endpoints Package - API v1エンドポイント実装

このパッケージには、KAGRA API v1の具体的なエンドポイント実装が含まれています。
各ファイルは特定の機能領域を担当し、関連するAPIエンドポイントを提供します。

エンドポイントファイル:
- auth.py: 認証・認可（ログイン、ログアウト、トークン管理）
- users.py: ユーザー管理（プロフィール、権限）
- admin.py: 管理機能（システム管理、ユーザー管理）
- search.py: 検索機能（全文検索、フィルタリング）
- nodes.py: Charaxyノード管理
- blocks.py: Charaxyブロック管理
- themes.py: Charaxyテーマ管理
- activity.py: Charaxyアクティビティ追跡

共通機能:
- 権限チェック（RBAC）
- 入力バリデーション
- エラーハンドリング
- レスポンス標準化
- 監査ログ記録
"""

# パッケージメタデータ
__package_name__ = "endpoints"
__description__ = "KAGRA API v1エンドポイント実装" 