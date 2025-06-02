from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Supabaseクライアント（シングルトン）
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Supabaseクライアントを取得（シングルトンパターン）"""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error("Failed to initialize Supabase client", error=str(e))
            raise
    
    return _supabase_client


def get_supabase_anon_client() -> Client:
    """匿名Supabaseクライアントを取得（フロントエンド用）"""
    try:
        return create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    except Exception as e:
        logger.error("Failed to create anonymous Supabase client", error=str(e))
        raise


class SupabaseService:
    """Supabaseサービスクラス"""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
    
    async def health_check(self) -> bool:
        """データベース接続確認"""
        try:
            result = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーIDでユーザー情報を取得"""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """メールアドレスでユーザー情報を取得"""
        try:
            result = self.client.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            return None
    
    def create_user_profile(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ユーザープロファイルを作成"""
        try:
            result = self.client.table("user_profiles").insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create user profile", error=str(e))
            return None
    
    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ユーザープロファイルを更新"""
        try:
            result = self.client.table("user_profiles").update(update_data).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update user profile", user_id=user_id, error=str(e))
            return None
    
    def get_nodes_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """ユーザーのノード一覧を取得"""
        try:
            result = (
                self.client.table("nodes")
                .select("*")
                .eq("creator_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to get nodes by user", user_id=user_id, error=str(e))
            return []
    
    def get_blocks_by_node(self, node_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """ノードのブロック一覧を取得"""
        try:
            result = (
                self.client.table("blocks")
                .select("*")
                .eq("node_id", node_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to get blocks by node", node_id=node_id, error=str(e))
            return []
    
    def search_embeddings(self, query_embedding: List[float], table: str = "node_embeddings", 
                         threshold: float = 0.5, limit: int = 10) -> List[Dict[str, Any]]:
        """ベクター検索を実行"""
        try:
            if table == "node_embeddings":
                result = self.client.rpc(
                    "match_node_documents",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": threshold,
                        "match_count": limit
                    }
                ).execute()
            else:  # block_embeddings
                result = self.client.rpc(
                    "match_documents",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": threshold,
                        "match_count": limit
                    }
                ).execute()
            
            return result.data or []
        except Exception as e:
            logger.error("Failed to search embeddings", table=table, error=str(e))
            return []


# グローバルサービスインスタンス
db_service = SupabaseService() 