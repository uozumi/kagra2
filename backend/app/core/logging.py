import structlog
import logging
from typing import List, Any, Dict
from app.core.config import settings


def setup_logging() -> None:
    """ログ設定を初期化"""
    # プロセッサーリストを動的に構築
    processors: List[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # 環境に応じてレンダラーを選択
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # structlogの設定
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 標準ライブラリのloggingレベルを設定
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(message)s"
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """構造化ロガーを取得"""
    return structlog.get_logger(name)


def log_request_info(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: str = None,
    **kwargs
) -> None:
    """リクエスト情報をログに記録"""
    logger = get_logger("request")
    
    log_data: Dict[str, Any] = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration": duration,
        **kwargs
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if status_code >= 400:
        logger.error("Request failed", **log_data)
    elif status_code >= 300:
        logger.warning("Request redirected", **log_data)
    else:
        logger.info("Request completed", **log_data)


def log_database_operation(
    operation: str,
    table: str,
    record_id: str = None,
    user_id: str = None,
    success: bool = True,
    error: str = None,
    **kwargs
) -> None:
    """データベース操作をログに記録"""
    logger = get_logger("database")
    
    log_data: Dict[str, Any] = {
        "operation": operation,
        "table": table,
        "success": success,
        **kwargs
    }
    
    if record_id:
        log_data["record_id"] = record_id
    if user_id:
        log_data["user_id"] = user_id
    if error:
        log_data["error"] = error
    
    if success:
        logger.info("Database operation completed", **log_data)
    else:
        logger.error("Database operation failed", **log_data)


def log_security_event(
    event_type: str,
    user_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    details: Dict[str, Any] = None,
    severity: str = "warning"
) -> None:
    """セキュリティイベントをログに記録"""
    logger = get_logger("security")
    
    log_data: Dict[str, Any] = {
        "event_type": event_type,
        "severity": severity
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    if user_agent:
        log_data["user_agent"] = user_agent
    if details:
        log_data.update(details)
    
    log_method = getattr(logger, severity.lower(), logger.warning)
    log_method("Security event", **log_data)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    tags: Dict[str, str] = None,
    **kwargs
) -> None:
    """パフォーマンスメトリクスをログに記録"""
    logger = get_logger("performance")
    
    log_data: Dict[str, Any] = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        **kwargs
    }
    
    if tags:
        log_data["tags"] = tags
    
    logger.info("Performance metric", **log_data)


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