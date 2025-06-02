import redis.asyncio as redis
from typing import Optional, Any
import json
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Redisクライアント
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Redisクライアントを取得"""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # 接続テスト
            await redis_client.ping()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis client", error=str(e))
            raise
    
    return redis_client


async def close_redis_client():
    """Redisクライアントを閉じる"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis client closed")


class RedisService:
    """Redisサービスクラス"""
    
    def __init__(self, client: Optional[redis.Redis] = None):
        self.client = client
    
    async def _get_client(self) -> redis.Redis:
        """クライアントを取得（遅延初期化）"""
        if self.client is None:
            self.client = await get_redis_client()
        return self.client
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """値を設定"""
        try:
            client = await self._get_client()
            
            # 辞書やリストの場合はJSON文字列に変換
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if ttl:
                await client.setex(key, ttl, value)
            else:
                await client.set(key, value)
            
            return True
        except Exception as e:
            logger.error("Failed to set Redis key", key=key, error=str(e))
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """値を取得"""
        try:
            client = await self._get_client()
            value = await client.get(key)
            
            if value is None:
                return default
            
            # JSON文字列の場合はパース
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error("Failed to get Redis key", key=key, error=str(e))
            return default
    
    async def delete(self, key: str) -> bool:
        """キーを削除"""
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Failed to delete Redis key", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """キーの存在確認"""
        try:
            client = await self._get_client()
            result = await client.exists(key)
            return result > 0
        except Exception as e:
            logger.error("Failed to check Redis key existence", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """TTLを設定"""
        try:
            client = await self._get_client()
            result = await client.expire(key, ttl)
            return result
        except Exception as e:
            logger.error("Failed to set Redis key TTL", key=key, ttl=ttl, error=str(e))
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """カウンターをインクリメント"""
        try:
            client = await self._get_client()
            result = await client.incr(key, amount)
            return result
        except Exception as e:
            logger.error("Failed to increment Redis key", key=key, error=str(e))
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """カウンターをデクリメント"""
        try:
            client = await self._get_client()
            result = await client.decr(key, amount)
            return result
        except Exception as e:
            logger.error("Failed to decrement Redis key", key=key, error=str(e))
            return None
    
    async def keys(self, pattern: str = "*") -> list:
        """パターンマッチするキー一覧を取得"""
        try:
            client = await self._get_client()
            keys = await client.keys(pattern)
            return keys
        except Exception as e:
            logger.error("Failed to get Redis keys", pattern=pattern, error=str(e))
            return []
    
    async def flushdb(self) -> bool:
        """データベースをクリア（開発環境のみ）"""
        if settings.ENVIRONMENT != "development":
            logger.warning("Attempted to flush Redis DB in non-development environment")
            return False
        
        try:
            client = await self._get_client()
            await client.flushdb()
            logger.info("Redis database flushed")
            return True
        except Exception as e:
            logger.error("Failed to flush Redis database", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Redis接続確認"""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False


# グローバルサービスインスタンス
redis_service = RedisService()

# 便利な関数
async def cache_get(key: str, default: Any = None) -> Any:
    """キャッシュから値を取得"""
    return await redis_service.get(key, default)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """キャッシュに値を設定"""
    return await redis_service.set(key, value, ttl or settings.CACHE_TTL)


async def cache_delete(key: str) -> bool:
    """キャッシュから値を削除"""
    return await redis_service.delete(key) 