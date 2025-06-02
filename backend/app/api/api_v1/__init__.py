"""
API Version 1 Package - KAGRA API v1エンドポイント

このパッケージには、KAGRA APIのバージョン1のエンドポイントが含まれています。
安定したAPIインターフェースを提供し、後方互換性を維持します。

エンドポイント分類:
- auth: 認証・認可関連
- users: ユーザー管理
- admin: 管理機能
- search: 検索機能
- charaxy: Charaxyシステム（ノード、ブロック、テーマ、アクティビティ）

特徴:
- 統一されたレスポンス形式
- 包括的なエラーハンドリング
- 権限ベースアクセス制御
- レート制限対応
- 詳細な監査ログ
"""

# パッケージメタデータ
__package_name__ = "api_v1"
__description__ = "KAGRA API バージョン1エンドポイント"
__version__ = "1.0.0"
__status__ = "stable" 