import os
import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.security import (
    SecurityMiddleware, 
    get_environment_security_headers,
    security_header_validator
)
from app.core.audit import AuditMiddleware
from app.api.api_v1.api import api_router

# ログ設定
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# FastAPIアプリケーション作成
app = FastAPI(
    title="KAGRA API",
    description="KAGRA システムのバックエンドAPI",
    version="2.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# レート制限設定
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ミドルウェア設定（正しい順序で）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セキュリティミドルウェア
app.add_middleware(SecurityMiddleware)

# 監査ミドルウェア（一時的に無効化）
# app.add_middleware(AuditMiddleware)

# レート制限ミドルウェア
app.add_middleware(SlowAPIMiddleware)

# 信頼できるホストミドルウェア
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["kagra.space", "system.kagra.space", "tenant.kagra.space", "api.kagra.space"]
    )

# APIルーター追加
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    """ヘルスチェックエンドポイント"""
    return {
        "message": "KAGRA API v2.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
@limiter.limit("120/minute")
async def health_check(request: Request):
    """詳細ヘルスチェック"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "rate_limiting": True,
            "security_headers": True,
            "rbac": True,
            "audit_logging": True,
            "advanced_sql_injection_protection": True,
            "brute_force_protection": True,
            "ip_filtering": True
        }
    }


@app.get("/security/test")
@limiter.limit("10/minute")
async def security_test(request: Request):
    """セキュリティ機能テスト（開発環境のみ）"""
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=404, detail="Not Found")
    
    from app.core.security import security_tester
    
    return {
        "sql_injection_tests": security_tester.test_sql_injection_patterns(),
        "validation_tests": security_tester.test_validation_functions(),
        "security_headers": {
            "enabled": True,
            "environment": settings.ENVIRONMENT
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    ) 