"""
KAGRA API メインアプリケーション

FastAPIを使用したKAGRAシステムのバックエンドAPIサーバー。
セキュリティ、認証、レート制限などの機能を統合したRESTful APIを提供します。
"""

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import APP_INFO
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import SecurityMiddleware
from app.core.audit import AuditMiddleware
from app.api.api_v1.api import api_router

# ログ設定を初期化
setup_logging()
logger = structlog.get_logger()


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成・設定
    
    Returns:
        設定済みのFastAPIアプリケーション
    """
    # FastAPIアプリケーション作成
    app = FastAPI(
        title=APP_INFO["title"],
        description=APP_INFO["description"],
        version=APP_INFO["version"],
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    )
    
    # レート制限設定
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    
    # ミドルウェア設定
    _setup_middleware(app)
    
    # エラーハンドラー設定
    _setup_error_handlers(app)
    
    # ルーター設定
    _setup_routes(app)
    
    logger.info("FastAPIアプリケーション初期化完了", 
                version=APP_INFO["version"], 
                environment=settings.ENVIRONMENT)
    
    return app


def _setup_middleware(app: FastAPI) -> None:
    """ミドルウェアを設定
    
    Args:
        app: FastAPIアプリケーション
    """
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # セキュリティミドルウェア
    app.add_middleware(SecurityMiddleware)
    
    # 監査ミドルウェア（本番環境では有効化を検討）
    if settings.ENVIRONMENT == "production":
        app.add_middleware(AuditMiddleware)
    
    # レート制限ミドルウェア
    app.add_middleware(SlowAPIMiddleware)
    
    # 信頼できるホストミドルウェア（本番環境のみ）
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                "kagra.space", 
                "system.kagra.space", 
                "tenant.kagra.space", 
                "api.kagra.space"
            ]
        )
    
    logger.info("ミドルウェア設定完了", environment=settings.ENVIRONMENT)


def _setup_error_handlers(app: FastAPI) -> None:
    """エラーハンドラーを設定
    
    Args:
        app: FastAPIアプリケーション
    """
    # レート制限エラーハンドラー
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # 一般的なHTTPエラーハンドラー
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTPエラーハンドラー"""
        logger.warning("HTTPエラー発生", 
                      status_code=exc.status_code, 
                      detail=exc.detail,
                      path=request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error"
                }
            }
        )
    
    # 予期しないエラーハンドラー
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """一般的なエラーハンドラー"""
        logger.error("予期しないエラー発生", 
                    error=str(exc),
                    path=request.url.path,
                    method=request.method)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "内部サーバーエラーが発生しました",
                    "type": "internal_error"
                }
            }
        )
    
    logger.info("エラーハンドラー設定完了")


def _setup_routes(app: FastAPI) -> None:
    """ルートを設定
    
    Args:
        app: FastAPIアプリケーション
    """
    # レート制限設定
    limiter = app.state.limiter
    
    @app.get("/")
    @limiter.limit("60/minute")
    async def root(request: Request):
        """ルートエンドポイント"""
        return {
            "message": f"{APP_INFO['title']} v{APP_INFO['version']}",
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None
        }
    
    @app.get("/health")
    @limiter.limit("120/minute")
    async def health_check(request: Request):
        """詳細ヘルスチェック"""
        return {
            "status": "healthy",
            "version": APP_INFO["version"],
            "environment": settings.ENVIRONMENT,
            "features": APP_INFO["features"]
        }
    
    # 開発環境専用エンドポイント
    if settings.ENVIRONMENT == "development":
        @app.get("/security/test")
        @limiter.limit("10/minute")
        async def security_test(request: Request):
            """セキュリティ機能テスト（開発環境のみ）"""
            try:
                from app.core.security import security_tester
                
                return {
                    "sql_injection_tests": security_tester.test_sql_injection_patterns(),
                    "validation_tests": security_tester.test_validation_functions(),
                    "security_headers": {
                        "enabled": True,
                        "environment": settings.ENVIRONMENT
                    }
                }
            except ImportError:
                logger.warning("セキュリティテスターが利用できません")
                return {
                    "error": "セキュリティテスター機能が利用できません",
                    "environment": settings.ENVIRONMENT
                }
    
    # APIルーター追加
    app.include_router(api_router, prefix="/api/v1")
    
    logger.info("ルート設定完了")


# アプリケーション作成
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("開発サーバー起動", 
                host="0.0.0.0", 
                port=8000, 
                reload=settings.ENVIRONMENT == "development")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    ) 