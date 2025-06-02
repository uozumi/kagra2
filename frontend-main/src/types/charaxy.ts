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
  deleted_at?: string | null;
  type?: string;
  tenant_id?: string | null;
  creator_id?: string | null;
  assignee_id?: string | null;
  metadata?: any;
}

export interface BlockTheme {
  id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
  creator_id?: string | null;
  is_suggested?: boolean | null;
  theme_category_id?: string | null;
}

export interface Node {
  id: string;
  title: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  user_id: string;
  type: string;
  is_public: boolean;
  parent_id?: string | null;
  sort_order: number;
  visibility_level: number;
  deleted_at?: string | null;
}

export interface EditState {
  title: boolean;
  content: boolean;
}

export interface EditValue {
  title: string;
  content: string;
} 