import { supabase } from './supabase';

const API_BASE_URL = '/api/v1';

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
  
  console.log('=== API Request Debug ===');
  console.log('Endpoint:', endpoint);
  console.log('Headers:', headers);
  console.log('Options:', options);
  
  // タイムアウト処理を追加
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒でタイムアウト
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.log('Error response data:', errorData);
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    const responseData = await response.json();
    console.log('Success response data:', responseData);
    return responseData;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('API request timeout:', endpoint);
      throw new Error('リクエストがタイムアウトしました');
    }
    throw error;
  }
};

// 汎用APIクライアント
export const apiClient = {
  get: async (endpoint: string) => {
    return apiRequest(endpoint, { method: 'GET' });
  },
  post: async (endpoint: string, data?: any) => {
    return apiRequest(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },
  delete: async (endpoint: string) => {
    return apiRequest(endpoint, { method: 'DELETE' });
  },
};

// システム管理API
export const systemApi = {
  // 全ユーザー取得
  getUsers: async () => {
    return apiRequest('/api/v1/admin/system/users');
  },

  // ユーザー権限確認
  getUserPermissions: async (userId: string) => {
    return apiRequest(`/api/v1/admin/system/users/${userId}/permissions`);
  },

  // システム管理者権限付与
  grantAdminPermission: async (userId: string) => {
    return apiRequest(`/api/v1/admin/system/users/${userId}/admin`, {
      method: 'POST',
    });
  },

  // システム管理者権限削除
  revokeAdminPermission: async (userId: string) => {
    return apiRequest(`/api/v1/admin/system/users/${userId}/admin`, {
      method: 'DELETE',
    });
  },
}; 