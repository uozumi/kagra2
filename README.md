# KAGRA システム v2.0

## ⚠️ 重要な注意事項（AI開発者向け）
- **このプロジェクトはDockerで動作しています**
- **`.env`ファイルには機密情報が含まれており、AIはアクセスできません**
- **バックエンド**: `docker logs kagra2-backend-1` でログ確認
- **フロントエンド**: ポート3000で動作（`kagra2-frontend-main-1`）
- **問題解決時は既存のDockerコンテナの状態を確認してから対応すること**
- **curlでのAPIテストは認証失敗するため、この方法は使わない**

# KAGRA v2.0 - Enterprise-Grade Architecture

KADOKAWA Group Ramblespace (KAGRA) の次世代エンタープライズアーキテクチャ実装

## 🏗️ アーキテクチャ概要

### マイクロサービス構成
- **バックエンド**: FastAPI + Python 3.11 + エンタープライズセキュリティ
- **データベース**: Supabase (PostgreSQL + pgvector + RLS)
- **フロントエンド**: 3つの独立したReact + TypeScript アプリ
- **インフラ**: Docker + Docker Compose (開発環境)
- **本番環境**: Google Cloud Platform
- **セキュリティ**: 多層防御システム + RBAC + 監査ログ

### サービス構成

| サービス | URL (開発) | URL (本番予定) | 説明 |
|---------|------------|---------------|------|
| メインアプリ | `http://localhost:3000` | `https://kagra.space` | キャラクシー機能・メインUI |
| システム管理 | `http://localhost:3001` | `https://system.kagra.space` | システム全体管理 |
| テナント管理 | `http://localhost:3002` | `https://tenant.kagra.space` | 組織・メンバー管理 |
| API サーバー | `http://localhost:8000` | `https://api.kagra.space` | RESTful API + セキュリティ |
| Redis | `localhost:6379` | - | キャッシュ・セッション |

## 🔒 エンタープライズセキュリティ機能

### 🛡️ 多層防御システム
- **レート制限**: SlowAPI による分単位の制限（全エンドポイント対応）
- **RBAC**: 6段階のロールベースアクセス制御
- **監査ログ**: 全操作の詳細記録とトラッキング
- **SQLインジェクション対策**: 24パターンの脅威検出 + パラメータ化クエリ
- **XSS対策**: 入力値サニタイゼーション + CSP
- **CSRF対策**: トークンベース保護
- **ブルートフォース対策**: ログイン試行回数制限
- **IP制限**: ホワイトリスト/ブラックリスト機能

### 🔐 RBAC (ロールベースアクセス制御)
```
SUPER_ADMIN    → 全システム管理権限
TENANT_ADMIN   → テナント管理権限
PROJECT_ADMIN  → プロジェクト管理権限
EDITOR         → 編集権限
VIEWER         → 閲覧権限
GUEST          → 限定閲覧権限
```

### 📊 監査ログシステム
- **24種類のアクション追跡**: CREATE, UPDATE, DELETE, READ, SEARCH等
- **詳細情報記録**: ユーザー、IP、タイムスタンプ、変更内容
- **自動記録**: 全エンドポイントで自動適用
- **セキュリティ分析**: 疑わしい活動の検出

### 🔍 高度なSQLインジェクション対策
- **24パターンの脅威検出**: SQL DML/DDL、NoSQL、XSS、パストラバーサル等
- **リアルタイム脅威分析**: Critical/High/Medium/Low のリスクレベル判定
- **ホワイトリスト方式**: 許可されたSQL演算子・関数のみ使用可能
- **パラメータ化クエリ**: 安全なクエリ構築機能
- **型別サニタイゼーション**: UUID、整数、メール、識別子、文字列

## 🚀 クイックスタート

### 前提条件
- Docker & Docker Compose
- Node.js 18+ (ローカル開発時)
- Supabase プロジェクト
- OpenAI API キー

### 1. 環境設定

```bash
# リポジトリをクローン
git clone <repository-url>
cd kagra2

# 環境変数を設定
cp env.example .env
# .envファイルを編集して必要な値を設定
```

### 2. 必須環境変数

```bash
# Supabase設定
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI設定
OPENAI_API_KEY=your_openai_api_key

# セキュリティ設定（オプション）
JWT_SECRET_KEY=your_jwt_secret_key
IP_WHITELIST=127.0.0.1,::1
ENVIRONMENT=development
```

### 3. 開発環境起動

```bash
# 全サービスを起動（推奨）
docker-compose --profile full up -d --build

# バックエンドのみ起動
docker-compose up -d backend redis

# フロントエンドも含めて起動
docker-compose --profile frontend up -d --build

# サービス状態確認
docker-compose ps

# ログ確認
docker-compose logs -f
```

### 4. アクセス確認

- **メインアプリ**: http://localhost:3000
- **システム管理**: http://localhost:3001  
- **テナント管理**: http://localhost:3002
- **API ドキュメント**: http://localhost:8000/docs
- **セキュリティテスト**: http://localhost:8000/security/test (開発環境のみ)

## 📁 プロジェクト構造

```
kagra2/
├── README.md                    # このファイル
├── docker-compose.yml          # 統合された開発環境設定
├── .env                         # 環境変数
├── env.example                  # 環境変数テンプレート
├── MIGRATION_GUIDE.md           # v1からの移行ガイド
│
├── backend/                     # FastAPI バックエンド
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI アプリケーション + セキュリティ統合
│       ├── core/               # 設定・データベース・認証・セキュリティ
│       │   ├── config.py       # 設定管理
│       │   ├── database.py     # Supabase接続
│       │   ├── auth.py         # 認証システム
│       │   ├── rbac.py         # ロールベースアクセス制御
│       │   ├── audit.py        # 監査ログシステム
│       │   └── security.py     # セキュリティミドルウェア・SQLインジェクション対策
│       ├── api/                # API エンドポイント
│       │   └── api_v1/
│       │       ├── api.py      # ルーター統合
│       │       └── endpoints/  # 機能別エンドポイント（全てセキュリティ対応済み）
│       │           ├── auth.py     # 認証 (レート制限: 3-10/分)
│       │           ├── users.py    # ユーザー管理 (レート制限: 10-30/分)
│       │           ├── nodes.py    # ノード (レート制限: 5-60/分)
│       │           ├── blocks.py   # ブロック (レート制限: 5-60/分)
│       │           ├── themes.py   # テーマ (レート制限: 5-60/分)
│       │           ├── activity.py # アクティビティ (レート制限: 20/分)
│       │           ├── admin.py    # 管理機能 (レート制限: 5-20/分)
│       │           └── search.py   # 検索機能 (レート制限: 30/分)
│       ├── models/             # Pydantic モデル
│       │   ├── user.py         # ユーザーモデル
│       │   ├── charaxy.py      # キャラクシー関連モデル
│       │   └── theme.py        # テーマモデル
│       └── services/           # ビジネスロジック
│           └── charaxy_service.py  # キャラクシーサービス層
│
├── frontend-main/              # メインフロントエンド
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts          # Vite設定 (port: 3000)
│   └── src/
│       ├── components/         # 共通コンポーネント
│       ├── contexts/           # React Context
│       ├── hooks/              # カスタムフック
│       ├── lib/                # ライブラリ・API
│       │   └── api.ts          # API呼び出しライブラリ
│       ├── pages/              # ページコンポーネント
│       │   ├── charaxy/        # キャラクシー機能
│       │   │   ├── CharaxyList.tsx    # キャラクシー一覧
│       │   │   ├── CharaxyDetail.tsx  # キャラクシー詳細
│       │   │   ├── ThemeList.tsx      # テーマ一覧
│       │   │   ├── ThemeDetail.tsx    # テーマ詳細
│       │   │   └── Activity.tsx       # みんなの更新
│       │   ├── Account.tsx     # アカウント設定
│       │   ├── Dashboard.tsx   # ダッシュボード
│       │   └── Landing.tsx     # ランディング
│       └── types/              # TypeScript型定義
│
├── frontend-system/            # システム管理フロントエンド
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts          # Vite設定 (port: 3001)
│   └── src/
│
├── frontend-tenant/            # テナント管理フロントエンド
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts          # Vite設定 (port: 3002)
│   └── src/
│
├── scripts/                    # 自動化スクリプト
│   ├── setup.sh               # 初期セットアップ
│   └── migrate_from_v1.sh      # v1からの移行
│
└── infrastructure/             # インフラ設定
    ├── gcp/                    # Google Cloud設定
    ├── terraform/              # Terraform設定
    └── nginx/                  # Nginx設定
```

## 🔧 開発コマンド

### Docker Compose プロファイル

```bash
# 🚀 全サービス起動（推奨）
docker-compose --profile full up -d --build

# 🔧 バックエンドのみ起動（API開発時）
docker-compose up -d backend redis

# 🎨 フロントエンドも起動（UI開発時）
docker-compose --profile frontend up -d --build

# 🏭 本番環境シミュレーション（Nginx含む）
docker-compose --profile production up -d --build
```

### 基本操作

```bash
# サービス状態確認
docker-compose ps

# ログ確認（全サービス）
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f backend
docker-compose logs -f frontend-main

# サービス停止
docker-compose down

# 完全クリーンアップ
docker-compose down -v --rmi all
```

### 個別サービス開発

```bash
# バックエンドのみ起動してフロントエンドはローカル実行
docker-compose up -d backend redis

# フロントエンド個別起動（ローカル）
cd frontend-main && npm run dev
cd frontend-system && npm run dev  
cd frontend-tenant && npm run dev
```

## 🔌 API エンドポイント

### 認証 (レート制限付き)
- `POST /api/v1/auth/register` - ユーザー登録 (3/分)
- `POST /api/v1/auth/login` - ユーザーログイン (5/分)
- `POST /api/v1/auth/logout` - ユーザーログアウト (10/分)
- `POST /api/v1/auth/refresh` - トークンリフレッシュ (10/分)
- `GET /api/v1/auth/me` - 現在のユーザー情報 (30/分)

### ユーザー管理 (RBAC + レート制限)
- `GET /api/v1/users/me` - 現在のユーザー詳細情報 (30/分)
- `PUT /api/v1/users/me` - 現在のユーザー情報更新 (10/分)

### キャラクシー - ノード管理 (所有者チェック + RBAC)
- `GET /api/v1/charaxy/nodes` - ユーザーのノード一覧 (30/分)
- `GET /api/v1/charaxy/nodes/{node_id}` - ノード詳細 (60/分)
- `POST /api/v1/charaxy/nodes` - ノード作成 (5/分)
- `PUT /api/v1/charaxy/nodes/{node_id}` - ノード更新 (10/分)
- `DELETE /api/v1/charaxy/nodes/{node_id}` - ノード削除 (5/分)

### キャラクシー - ブロック管理 (所有者チェック + RBAC)
- `GET /api/v1/charaxy/nodes/{node_id}/blocks` - ノードのブロック一覧 (30/分)
- `GET /api/v1/charaxy/blocks/{block_id}` - ブロック詳細 (60/分)
- `POST /api/v1/charaxy/blocks` - ブロック作成 (5/分)
- `PUT /api/v1/charaxy/blocks/{block_id}` - ブロック更新 (10/分)
- `DELETE /api/v1/charaxy/blocks/{block_id}` - ブロック削除 (5/分)
- `PUT /api/v1/charaxy/blocks/reorder` - ブロック順序変更 (10/分)
- `PUT /api/v1/charaxy/blocks/{block_id}/theme` - ブロックテーマ設定 (15/分)

### キャラクシー - テーマ管理 (所有者チェック + RBAC)
- `GET /api/v1/charaxy/themes` - テーマ一覧 (30/分)
- `GET /api/v1/charaxy/themes/{theme_id}` - テーマ詳細 (60/分)
- `GET /api/v1/charaxy/themes/{theme_id}/blocks` - テーマ別ブロック一覧 (30/分)
- `POST /api/v1/charaxy/themes` - テーマ作成 (5/分)
- `PUT /api/v1/charaxy/themes/{theme_id}` - テーマ更新 (10/分)

### キャラクシー - アクティビティ
- `GET /api/v1/charaxy/activity` - ユーザーアクティビティ (20/分)

### 検索機能
- `POST /api/v1/search/` - ベクター検索 (30/分)

### 管理機能 (管理者権限必須)
- `GET /api/v1/admin/` - 管理機能 (20/分)
- `GET /api/v1/admin/system/users` - 全ユーザー取得 (20/分)
- `GET /api/v1/admin/system/users/{user_id}/permissions` - ユーザー権限取得 (10/分)
- `POST /api/v1/admin/system/users/{user_id}/admin` - 管理者権限付与 (5/分)
- `DELETE /api/v1/admin/system/users/{user_id}/admin` - 管理者権限削除 (5/分)

### セキュリティ機能 (開発環境のみ)
- `GET /api/v1/security/test` - セキュリティ機能テスト (10/分)

## ✨ 実装済み機能

### 🎯 キャラクシー機能（メインアプリ）
- **ノード管理**: キャラクシーの作成・編集・削除・公開設定
- **ブロック管理**: ブロックの作成・編集・削除・並び替え
- **テーマ機能**: テーマ作成・ブロックのテーマ設定・テーマ別表示
- **アクティビティ**: 他ユーザーの更新情報表示
- **権限管理**: 所有者のみ編集可能な権限制御
- **レスポンシブUI**: Material-UIによるモダンなインターフェース

### 🔐 認証・ユーザー管理
- **Supabase認証**: メール・パスワード認証
- **ユーザープロファイル**: 名前・アバター・所属情報管理
- **RBAC**: 6段階のロールベースアクセス制御
- **セッション管理**: JWT トークンベース認証
- **ブルートフォース対策**: ログイン試行回数制限

### 🛡️ エンタープライズセキュリティ
- **レート制限**: 全エンドポイントに分単位の制限
- **SQLインジェクション対策**: 24パターンの脅威検出
- **XSS対策**: 入力値サニタイゼーション + CSP
- **CSRF対策**: トークンベース保護
- **監査ログ**: 全操作の詳細記録
- **IP制限**: ホワイトリスト/ブラックリスト
- **セキュリティヘッダー**: 環境別最適化

### 🏗️ アーキテクチャ
- **サービス層分離**: ビジネスロジックの集約
- **API ライブラリ**: フロントエンドでの統一されたAPI呼び出し
- **型安全性**: TypeScript による厳密な型定義
- **エラーハンドリング**: 構造化ログとエラー処理
- **監査ミドルウェア**: 全リクエストの自動記録

## 🛠️ 技術スタック

### バックエンド
- **FastAPI** 0.104.1 - 高性能Web API フレームワーク
- **Python** 3.11 - プログラミング言語
- **Supabase** 2.8.0 - PostgreSQL + 認証 + リアルタイム + RLS
- **Redis** 7 - キャッシュ・セッション管理
- **Pydantic** 2.5.0 - データバリデーション
- **Structlog** 23.2.0 - 構造化ログ
- **SlowAPI** 0.1.9 - レート制限
- **python-jose** 3.3.0 - JWT認証

### フロントエンド
- **React** 19 - UIライブラリ
- **TypeScript** 5.8.3 - 型安全なJavaScript
- **Vite** 6.3.5 - 高速ビルドツール
- **Material-UI** 5.14.20 - UIコンポーネントライブラリ
- **React Router** 6.20.1 - ルーティング
- **Supabase Client** 2.38.4 - データベース・認証クライアント

### AI/ML
- **OpenAI API** 1.3.7 - GPT・Embedding
- **pgvector** - ベクター検索（Supabase）

### セキュリティ
- **Row Level Security (RLS)** - データベースレベルセキュリティ
- **RBAC** - ロールベースアクセス制御
- **監査ログ** - 全操作記録
- **レート制限** - DDoS対策
- **SQLインジェクション対策** - 多層防御
- **セキュリティヘッダー** - XSS/CSRF対策

### インフラ
- **Docker** - コンテナ化
- **Google Cloud Platform** - 本番環境
- **Cloud Run** - サーバーレスコンテナ
- **Cloud SQL** - マネージドPostgreSQL

## 🔄 v1からの主な変更点

1. **アーキテクチャ**: モノリス → マイクロサービス
2. **認証**: Firebase Auth → Supabase Auth + RBAC
3. **セキュリティ**: 基本的な保護 → エンタープライズレベル多層防御
4. **フロントエンド**: 単一アプリ → 3つの独立アプリ
5. **URL構造**: パス分離 → サブドメイン分離
6. **インフラ**: Firebase Hosting → Google Cloud Platform
7. **開発環境**: ローカル → Docker Compose
8. **API設計**: RESTful API の体系化 + セキュリティ統合
9. **コード構造**: サービス層・モデル層の分離
10. **監査機能**: なし → 全操作記録システム

## 📋 開発ロードマップ

### ✅ 完了済み (100%)
- [x] 基本アーキテクチャ構築
- [x] Supabase認証システム + RLS設定
- [x] キャラクシー基本機能（CRUD）
- [x] テーマ機能
- [x] アクティビティ機能
- [x] ユーザー管理機能
- [x] APIエンドポイント体系化
- [x] フロントエンドUI実装
- [x] **エンタープライズセキュリティシステム**
  - [x] RBAC (6段階ロール)
  - [x] 監査ログシステム (24種類アクション)
  - [x] レート制限 (全エンドポイント)
  - [x] SQLインジェクション対策 (24パターン検出)
  - [x] XSS対策 (入力値サニタイゼーション + CSP)
  - [x] CSRF対策 (トークンベース)
  - [x] ブルートフォース対策
  - [x] IP制限機能
  - [x] セキュリティヘッダー (環境別最適化)
  - [x] 入力値サニタイゼーション
  - [x] セキュリティスコアリング (95/100 Excellent)

### 🚧 進行中
- [ ] システム管理アプリ実装
- [ ] テナント管理アプリ実装
- [ ] ベクター検索機能
- [ ] AI機能統合

### 📅 今後の予定
- [ ] 既存データの移行スクリプト
- [ ] GCP デプロイ設定
- [ ] CI/CD パイプライン
- [ ] モニタリング・ログ設定
- [ ] セキュリティ監査
- [ ] パフォーマンス最適化

## 🔒 セキュリティ機能詳細

### レート制限設定
```python
# 認証エンドポイント
register: 3/分, login: 5/分, logout: 10/分

# データ操作エンドポイント  
GET: 30-60/分, POST: 5/分, PUT: 10/分, DELETE: 5/分

# 管理機能
admin: 5-20/分 (管理者権限必須)
```

### RBAC権限マトリックス
```
機能              SUPER  TENANT PROJECT EDITOR VIEWER GUEST
システム管理        ✓      -      -       -      -      -
テナント管理        ✓      ✓      -       -      -      -
プロジェクト管理    ✓      ✓      ✓       -      -      -
ノード作成/編集     ✓      ✓      ✓       ✓      -      -
ブロック作成/編集   ✓      ✓      ✓       ✓      -      -
テーマ作成/編集     ✓      ✓      ✓       ✓      -      -
閲覧               ✓      ✓      ✓       ✓      ✓      ✓
```

### 監査ログ記録項目
- **ユーザー情報**: ID, 名前, ロール
- **操作情報**: アクション, リソースタイプ, リソースID
- **技術情報**: IP, User-Agent, タイムスタンプ
- **変更内容**: 変更前後のデータ (機密情報除く)

## 🤝 開発ガイド

### 新機能追加の流れ
1. **バックエンド**: 
   - `app/models/` にPydanticモデル追加
   - `app/services/` にビジネスロジック実装
   - `app/api/api_v1/endpoints/` にエンドポイント追加
   - **セキュリティ**: `@require_permission`, `@limiter.limit`, `@audit_log` デコレータ追加
2. **フロントエンド**:
   - `src/lib/api.ts` にAPI呼び出し関数追加
   - `src/types/` に型定義追加
   - `src/pages/` にページコンポーネント実装
3. **テスト・デバッグ**:
   - API ドキュメント確認: `http://localhost:8000/docs`
   - セキュリティテスト: `http://localhost:8000/security/test`
   - ログ確認: `docker-compose logs -f backend`

### セキュリティ実装ガイド
```python
# エンドポイントのセキュリティ実装例
@router.post("/example")
@limiter.limit("5/minute")  # レート制限
@require_permission(Permission.EXAMPLE_CREATE)  # RBAC
@audit_log(action=AuditAction.EXAMPLE_CREATE, resource_type="example")  # 監査ログ
async def create_example(
    request: Request,
    data: ExampleCreate,
    current_user: User = Depends(get_current_user)
):
    # 入力値サニタイゼーション
    data.title = query_sanitizer.sanitize_string(data.title)
    
    # ビジネスロジック
    result = service.create_example(data, current_user.id)
    
    return result
```

### コーディング規約
- **TypeScript**: 厳密な型定義を使用
- **API設計**: RESTful な設計原則に従う
- **セキュリティ**: 全エンドポイントにセキュリティ機能実装必須
- **エラーハンドリング**: 適切なHTTPステータスコードとメッセージ
- **ログ**: 構造化ログによる詳細な情報記録

### デバッグ
- **バックエンドログ**: `docker-compose logs -f backend`
- **フロントエンドログ**: ブラウザの開発者ツール
- **データベース**: Supabase ダッシュボード
- **API テスト**: `http://localhost:8000/docs`
- **セキュリティテスト**: `http://localhost:8000/security/test`

## 📊 セキュリティスコア

現在のセキュリティレベル: **95/100 (Excellent)**

### 実装済みセキュリティ機能
- ✅ レート制限 (全エンドポイント)
- ✅ RBAC (6段階ロール)
- ✅ 監査ログ (24種類アクション)
- ✅ SQLインジェクション対策 (24パターン)
- ✅ XSS対策 (入力値サニタイゼーション + CSP)
- ✅ CSRF対策 (トークンベース)
- ✅ ブルートフォース対策
- ✅ IP制限機能
- ✅ セキュリティヘッダー (環境別最適化)
- ✅ Row Level Security (RLS)

## 📞 サポート

問題が発生した場合：
1. ログを確認（`docker-compose logs -f`）
2. 環境変数を確認（`.env` ファイル）
3. Docker コンテナの状態を確認（`docker-compose ps`）
4. `MIGRATION_GUIDE.md` を参照
5. API ドキュメントを確認（`http://localhost:8000/docs`）
6. セキュリティテストを実行（`http://localhost:8000/security/test`）

### よくある問題と解決方法

#### フロントエンドが起動しない
```bash
# package.jsonのスクリプト確認
cd frontend-system && npm run dev  # "start"ではなく"dev"を使用

# 依存関係の再インストール
cd frontend-system && npm install
```

#### セキュリティエラー
```bash
# セキュリティ機能のテスト
curl http://localhost:8000/security/test

# 監査ログの確認
docker-compose logs -f backend | grep "audit"
```

#### データベース接続エラー
```bash
# Supabase設定の確認
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# RLS設定の確認
# Supabaseダッシュボードでポリシー設定を確認
```

## 🧪 APIテスト方法

### 認証について
- **すべてのAPIエンドポイントは認証が必要です**
- `curl`での直接テストは403 Forbiddenエラーになります
- フロントエンド経由でのテストを推奨します

### 開発用テストユーザー
```
メールアドレス: test@example.com
ユーザーID: 0a4691d7-29ae-426c-813c-42a6383717f2
```

### APIエンドポイント一覧

#### ノード関連
- `GET /api/v1/charaxy/nodes/` → ノード一覧
- `GET /api/v1/charaxy/nodes/{node_id}/` → ノード詳細
- `POST /api/v1/charaxy/nodes/` → ノード作成
- `PUT /api/v1/charaxy/nodes/{node_id}/` → ノード更新
- `DELETE /api/v1/charaxy/nodes/{node_id}/` → ノード削除

#### ブロック関連
- `GET /api/v1/charaxy/nodes/{node_id}/blocks/` → ノードのブロック一覧
- `GET /api/v1/charaxy/blocks/{block_id}/` → ブロック詳細
- `POST /api/v1/charaxy/blocks/` → ブロック作成
- `PUT /api/v1/charaxy/blocks/{block_id}/` → ブロック更新
- `DELETE /api/v1/charaxy/blocks/{block_id}/` → ブロック削除
- `PUT /api/v1/charaxy/blocks/reorder/` → ブロック並べ替え
- `PUT /api/v1/charaxy/blocks/{block_id}/theme/` → ブロックテーマ設定

#### テーマ関連
- `GET /api/v1/charaxy/themes/` → テーマ一覧
- `GET /api/v1/charaxy/themes/{theme_id}/` → テーマ詳細
- `GET /api/v1/charaxy/themes/{theme_id}/blocks/` → テーマのブロック一覧
- `POST /api/v1/charaxy/themes/` → テーマ作成
- `PUT /api/v1/charaxy/themes/{theme_id}/` → テーマ更新

#### アクティビティ関連
- `GET /api/v1/charaxy/activity/` → アクティビティ取得

### 重要な注意事項
- **末尾スラッシュが必要**: すべてのエンドポイントは末尾に`/`が必要です
- **307リダイレクト回避**: 末尾スラッシュがないと307 Temporary Redirectが発生します
- **認証必須**: フロントエンド経由でSupabase認証を通してアクセスしてください

### トラブルシューティング
- `403 Forbidden` → 認証が必要です
- `307 Temporary Redirect` → 末尾スラッシュを追加してください
- `404 Not Found` → エンドポイントパスを確認してください
- `400 Bad Request` → ルーティング競合の可能性があります

---

**KAGRA v2.0** - Enterprise-Grade Security + Supabase + FastAPI + React + GCP 