import structlog
import logging
import sys
from typing import Any, Dict

from app.core.config import settings


def setup_logging() -> None:
    """ログ設定を初期化"""
    
    # ログレベル設定
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 標準ログ設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # structlogの設定
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
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" 
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """ロガーを取得"""
    return structlog.get_logger(name)


class LoggerMixin:
    """ログ機能を提供するMixin"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        return structlog.get_logger(self.__class__.__name__)


def log_request_response(func):
    """リクエスト・レスポンスをログ出力するデコレータ"""
    async def wrapper(*args, **kwargs):
        logger = structlog.get_logger()
        
        # リクエストログ
        logger.info(
            "API request",
            function=func.__name__,
            args=str(args)[:200],  # 長すぎる場合は切り詰め
            kwargs={k: str(v)[:100] for k, v in kwargs.items()}
        )
        
        try:
            result = await func(*args, **kwargs)
            
            # 成功レスポンスログ
            logger.info(
                "API response success",
                function=func.__name__,
                response_type=type(result).__name__
            )
            
            return result
            
        except Exception as e:
            # エラーレスポンスログ
            logger.error(
                "API response error",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    return wrapper 