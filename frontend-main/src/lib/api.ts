import { supabase } from './supabase';

// 強制更新: 2024-12-19 12:45 - キャッシュ問題解決のため
const API_BASE_URL = import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1';
console.log('🔥 API_BASE_URL loaded:', API_BASE_URL);

// キャッシュバスター: 2024-12-19 12:41

// 認証ヘッダーを取得
const getAuthHeaders = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error('認証が必要です');
  }
  
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  };
};

// APIリクエストのヘルパー
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const headers = await getAuthHeaders();
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
};

// ノード関連API
export const nodeApi = {
  // ノード一覧取得
  getNodes: async () => {
    return apiRequest('/charaxy/nodes/');
  },

  // ノード詳細取得
  getNode: async (nodeId: string) => {
    return apiRequest(`/charaxy/nodes/${nodeId}/`);
  },

  // ノード作成
  createNode: async (data: { title: string; description?: string; type?: string; is_public?: boolean }) => {
    return apiRequest('/charaxy/nodes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // ノード更新
  updateNode: async (nodeId: string, data: { title?: string; description?: string; type?: string; is_public?: boolean }) => {
    return apiRequest(`/charaxy/nodes/${nodeId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // ノード削除
  deleteNode: async (nodeId: string) => {
    return apiRequest(`/charaxy/nodes/${nodeId}/`, {
      method: 'DELETE',
    });
  },
};

// ブロック関連API
export const blockApi = {
  // ブロック一覧取得
  getBlocks: async (nodeId: string) => {
    return apiRequest(`/charaxy/nodes/${nodeId}/blocks/`);
  },

  // ブロック詳細取得
  getBlock: async (nodeId: string, blockId: string) => {
    return apiRequest(`/charaxy/blocks/${blockId}/`);
  },

  // ブロック作成
  createBlock: async (data: { title: string; content?: string; node_id: string; block_theme_id?: string }) => {
    return apiRequest('/charaxy/blocks/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // ブロック更新
  updateBlock: async (blockId: string, data: { title?: string; content?: string; sort_order?: number; block_theme_id?: string }) => {
    return apiRequest(`/charaxy/blocks/${blockId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // ブロック削除
  deleteBlock: async (blockId: string) => {
    return apiRequest(`/charaxy/blocks/${blockId}/`, {
      method: 'DELETE',
    });
  },

  // ブロック並べ替え
  reorderBlocks: async (blockIds: string[]) => {
    return apiRequest('/charaxy/blocks/reorder/', {
      method: 'PUT',
      body: JSON.stringify(blockIds),
    });
  },

  // ブロックにテーマ設定
  setBlockTheme: async (blockId: string, themeId?: string) => {
    return apiRequest(`/charaxy/blocks/${blockId}/theme/`, {
      method: 'PUT',
      body: JSON.stringify({ theme_id: themeId }),
    });
  },
};

// テーマ関連API
export const themeApi = {
  // テーマ一覧取得
  getThemes: async () => {
    return apiRequest('/charaxy/themes/');
  },

  // テーマ詳細取得
  getTheme: async (themeId: string) => {
    return apiRequest(`/charaxy/themes/${themeId}/`);
  },

  // テーマのブロック一覧取得
  getThemeBlocks: async (themeId: string) => {
    return apiRequest(`/charaxy/themes/${themeId}/blocks/`);
  },

  // テーマ作成
  createTheme: async (data: { title: string }) => {
    return apiRequest('/charaxy/themes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // テーマ更新
  updateTheme: async (themeId: string, data: { title: string }) => {
    return apiRequest(`/charaxy/themes/${themeId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

// アクティビティ関連API
export const activityApi = {
  // アクティビティ取得
  getActivity: async () => {
    return apiRequest('/charaxy/activity/');
  },
}; 