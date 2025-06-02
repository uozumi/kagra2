from supabase import create_client, Client
from typing import Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Supabaseクライアント
supabase: Optional[Client] = None


def get_supabase_client() -> Client:
    """Supabaseクライアントを取得"""
    global supabase
    
    if supabase is None:
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("Supabase client initialized")
    
    return supabase


def get_supabase_anon_client() -> Client:
    """匿名Supabaseクライアントを取得（フロントエンド用）"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )


# グローバルクライアントインスタンス
supabase = get_supabase_client()


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
    
    def get_user_by_id(self, user_id: str):
        """ユーザーIDでユーザー情報を取得"""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
            return None
    
    def get_user_by_email(self, email: str):
        """メールアドレスでユーザー情報を取得"""
        try:
            result = self.client.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            return None
    
    def create_user_profile(self, user_data: dict):
        """ユーザープロファイルを作成"""
        try:
            result = self.client.table("user_profiles").insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create user profile", error=str(e))
            return None
    
    def update_user_profile(self, user_id: str, update_data: dict):
        """ユーザープロファイルを更新"""
        try:
            result = self.client.table("user_profiles").update(update_data).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update user profile", user_id=user_id, error=str(e))
            return None
    
    def get_nodes_by_user(self, user_id: str, limit: int = 20, offset: int = 0):
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
            return result.data
        except Exception as e:
            logger.error("Failed to get nodes by user", user_id=user_id, error=str(e))
            return []
    
    def get_blocks_by_node(self, node_id: str, limit: int = 20, offset: int = 0):
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
            return result.data
        except Exception as e:
            logger.error("Failed to get blocks by node", node_id=node_id, error=str(e))
            return []
    
    def search_embeddings(self, query_embedding: list, table: str = "node_embeddings", 
                         threshold: float = 0.5, limit: int = 10):
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
            
            return result.data
        except Exception as e:
            logger.error("Failed to search embeddings", table=table, error=str(e))
            return []


# グローバルサービスインスタンス
db_service = SupabaseService() 