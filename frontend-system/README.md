# KAGRA System Admin Frontend

このプロジェクトは、KAGRAシステムの管理者向けフロントエンドアプリケーションです。
Supabase認証とFastAPI バックエンドを使用しています。

## 機能

- システム管理者ダッシュボード
- ユーザー管理（システム管理者権限の付与・削除）
- 認証・認可機能

## 技術スタック

- React 19
- TypeScript
- Material-UI (MUI)
- React Router
- Supabase (認証のみ)
- FastAPI (バックエンドAPI)

## セットアップ

### 方法1: ローカル環境での実行

#### 1. 依存関係のインストール

```bash
npm install
```

#### 2. 環境変数の設定

プロジェクトルートの`.env`ファイルに以下の環境変数を設定してください：

```env
# Supabase設定
VITE_SUPABASE_URL=http://localhost:8000
VITE_SUPABASE_ANON_KEY=dummy-key
```

#### 3. 開発サーバーの起動

```bash
npm run dev
```

アプリケーションは `http://localhost:3001` で起動します。

### 方法2: Docker環境での実行（推奨）

このプロジェクトはKAGRAプロジェクト全体のDocker設定の一部として動作します。

#### 1. プロジェクトルートでの実行

```bash
# プロジェクトルートディレクトリに移動
cd /Users/uozumi-y/Desktop/kagra2

# システム管理フロントエンドのみを起動
docker-compose up frontend-system

# または、バックエンドと一緒に起動
docker-compose up backend frontend-system

# 全サービスを起動
docker-compose --profile full up
```

#### 2. バックグラウンドでの実行

```bash
# バックグラウンドで実行
docker-compose up -d frontend-system

# 停止
docker-compose down
```

#### 3. 開発時のホットリロード

- ソースコードの変更は自動的にコンテナに反映されます
- `node_modules`はコンテナ内で管理されるため、ローカルの`node_modules`と競合しません

## API エンドポイント

このフロントエンドは以下のFastAPI エンドポイントを使用します：

- `GET /api/v1/system/users` - 全ユーザー取得
- `POST /api/v1/system/users/{user_id}/admin` - システム管理者権限付与
- `DELETE /api/v1/system/users/{user_id}/admin` - システム管理者権限削除
- `GET /api/v1/system/users/{user_id}/permissions` - ユーザー権限確認

## ページ構成

- `/` - ダッシュボード
- `/members` - メンバー管理
- `/login` - ログインページ

## 認証・認可

- Supabaseによる認証
- システム管理者権限が必要
- 権限チェックはFastAPI経由で実行

## 移植元

このプロジェクトは `/Users/uozumi-y/Desktop/kagra2/kagra/main2/src/pages/admin-system/` から移植されました。

主な変更点：
- Supabase直接アクセスからFastAPI経由のアクセスに変更
- 権限チェックロジックをFastAPI側に移行
- APIクライアントの実装を追加

## Docker設定

### ファイル構成

- `Dockerfile` - Dockerイメージの定義
- `.dockerignore` - Dockerイメージから除外するファイル
- プロジェクトルートの`docker-compose.yml` - 全体のDocker設定

### ポート設定

- システム管理フロントエンド: `3001`
- メインフロントエンド: `3000`
- テナント管理フロントエンド: `3002`
- バックエンドAPI: `8000`

### ネットワーク

`kagra-network`を使用して、他のKAGRAサービスと通信します。

### プロファイル

Docker Composeでは以下のプロファイルが利用可能です：

- `frontend` - フロントエンドサービスのみ
- `full` - 全サービス
- `production` - 本番環境用（Nginx含む）

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config({
  extends: [
    // Remove ...tseslint.configs.recommended and replace with this
    ...tseslint.configs.recommendedTypeChecked,
    // Alternatively, use this for stricter rules
    ...tseslint.configs.strictTypeChecked,
    // Optionally, add this for stylistic rules
    ...tseslint.configs.stylisticTypeChecked,
  ],
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
})
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config({
  plugins: {
    // Add the react-x and react-dom plugins
    'react-x': reactX,
    'react-dom': reactDom,
  },
  rules: {
    // other rules...
    // Enable its recommended typescript rules
    ...reactX.configs['recommended-typescript'].rules,
    ...reactDom.configs.recommended.rules,
  },
})
```
