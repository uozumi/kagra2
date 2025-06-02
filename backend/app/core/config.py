from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # 基本設定
    PROJECT_NAME: str = "KAGRA API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API設定
    API_V1_STR: str = "/api/v1"
    
    # CORS設定（環境変数から文字列として受け取る）
    CORS_ORIGINS_STR: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,https://kagra.space,https://system.kagra.space,https://tenant.kagra.space"
    
    # Supabase設定（必須）
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: Optional[str] = None  # JWT検証用秘密鍵
    
    # OpenAI設定（必須）
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 1000
    
    # Redis設定
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # JWT設定
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # セキュリティ設定
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12
    
    # ファイルアップロード設定
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg",
        "image/png", 
        "image/gif",
        "application/pdf"
    ]
    UPLOAD_DIR: str = "uploads"
    
    # レート制限設定
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # GCP設定
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: str = "asia-northeast1"
    GCP_SERVICE_ACCOUNT_KEY: Optional[str] = None
    
    # 監視設定
    SENTRY_DSN: Optional[str] = None
    GOOGLE_CLOUD_LOGGING_ENABLED: bool = False
    
    # メール設定
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # データベース設定
    DATABASE_URL: Optional[str] = None
    
    # キャッシュ設定
    CACHE_TTL: int = 300  # 5分
    CACHE_MAX_SIZE: int = 1000
    
    # AI/ML設定
    EMBEDDING_DIMENSION: int = 1536  # text-embedding-3-small
    SIMILARITY_THRESHOLD: float = 0.5
    MAX_SEARCH_RESULTS: int = 10
    
    # ページネーション設定
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """CORS_ORIGINS_STRをリストに変換"""
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 環境に応じた設定調整
        if self.ENVIRONMENT == "production":
            self.DEBUG = False
            self.LOG_LEVEL = "WARNING"
        elif self.ENVIRONMENT == "development":
            self.DEBUG = True
            self.LOG_LEVEL = "DEBUG"
            
        # CORS設定の環境別調整
        if self.ENVIRONMENT == "development":
            self.CORS_ORIGINS.extend([
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002"
            ])


# グローバル設定インスタンス
settings = Settings() 