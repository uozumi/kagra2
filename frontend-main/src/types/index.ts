// キャラクシー関連の型定義

export interface Block {
  id: string;
  title: string;
  content?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  block_theme_id?: string;
  node_id?: string;
  sort_order?: number;
  node?: { id: string; title: string; user_id: string };
  user?: { id: string; name: string };
  block_theme?: { id: string; title: string };
  node_title?: string;
  user_name?: string;
}

export interface BlockTheme {
  id: string;
  title: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  creator_id?: string;
  is_suggested?: boolean;
  theme_category_id?: string;
  category?: { id: string; title: string };
  block_count?: number;
}

export interface EditState {
  title: boolean;
  content: boolean;
}

export interface EditValue {
  title: string;
  content: string;
}

// ノード関連の型定義
export interface Node {
  id: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  charaxy_id: string;
  sort_order?: number;
  is_public: boolean;
  user_name?: string;
  user_avatar?: string;
}

// キャラクシー関連の型定義
export interface Charaxy {
  id: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  is_public: boolean;
  theme_id?: string;
}

// テーマ関連の型定義
export interface Theme {
  id: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  is_public: boolean;
}

// ユーザー関連の型定義
export interface UserProfile {
  id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

// 権限関連の型定義
export interface UserPermission {
  user_id: string;
  permission_level: number;
  tenant_id?: string;
  is_system_admin: boolean;
  is_tenant_admin: boolean;
} 