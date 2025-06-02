"""
API Package - RESTful APIエンドポイント

このパッケージには、KAGRAシステムのRESTful APIエンドポイントが含まれています。
バージョン管理されたAPIを提供し、クライアントアプリケーションとの通信を担当します。

構造:
- api_v1/: APIバージョン1のエンドポイント群
  - endpoints/: 機能別エンドポイント実装
  - api.py: ルーター統合設定

API設計原則:
- RESTful設計に準拠
- 適切なHTTPステータスコード使用
- 統一されたエラーレスポンス形式
- レート制限とセキュリティ対策
- 権限ベースアクセス制御
"""

# パッケージメタデータ
__package_name__ = "api"
__description__ = "KAGRA API RESTfulエンドポイントパッケージ"
__api_version__ = "v1" 