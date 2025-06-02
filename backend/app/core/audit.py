from enum import Enum
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import json
import structlog
from functools import wraps
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.database import get_supabase_client
from app.models.user import User

logger = structlog.get_logger()

class AuditAction(str, Enum):
    """監査対象のアクション"""
    # 認証関連
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    PASSWORD_CHANGE = "auth.password_change"
    
    # ユーザー管理
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"
    
    # テナント管理
    TENANT_CREATE = "tenant.create"
    TENANT_UPDATE = "tenant.update"
    TENANT_DELETE = "tenant.delete"
    
    # プロジェクト管理
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    
    # ノード管理
    NODE_CREATE = "node.create"
    NODE_UPDATE = "node.update"
    NODE_DELETE = "node.delete"
    
    # ブロック管理
    BLOCK_CREATE = "block.create"
    BLOCK_UPDATE = "block.update"
    BLOCK_DELETE = "block.delete"
    BLOCK_REORDER = "block.reorder"
    
    # テーマ管理
    THEME_CREATE = "theme.create"
    THEME_UPDATE = "theme.update"
    THEME_DELETE = "theme.delete"
    
    # システム管理
    SYSTEM_CONFIG_UPDATE = "system.config_update"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    
    # セキュリティ
    SECURITY_VIOLATION = "security.violation"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "security.unauthorized_access"
    
    # 一般的なアクション
    READ = "read"
    SEARCH = "search"

class AuditLevel(str, Enum):
    """監査ログレベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditLogger:
    """監査ログ記録システム"""
    
    def __init__(self):
        self.supabase = None
    
    def _get_supabase(self):
        """Supabaseクライアントを取得"""
        if not self.supabase:
            self.supabase = get_supabase_client()
        return self.supabase
    
    def log_audit(
        self,
        action: AuditAction,
        user: Optional[User] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        level: AuditLevel = AuditLevel.INFO,
        success: bool = True
    ):
        """監査ログを記録"""
        try:
            # リクエスト情報を取得
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            # 監査ログデータを構築
            audit_data = {
                "action": action.value,
                "user_id": user.id if user else None,
                "user_email": user.email if user else None,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": json.dumps(details) if details else None,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "level": level.value,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # 構造化ログに出力（audit_logsテーブルが作成されるまでの暫定対応）
            logger.info(
                "Audit log recorded",
                action=action.value,
                user_id=user.id if user else None,
                resource_type=resource_type,
                resource_id=resource_id,
                level=level.value,
                success=success,
                details=details,
                ip_address=ip_address
            )
            
        except Exception as e:
            logger.error("監査ログ記録エラー", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        action=action.value,
                        user_id=user.id if user else None,
                        resource_type=resource_type,
                        resource_id=resource_id)
    
    def log_authentication(
        self,
        action: AuditAction,
        user: Optional[User] = None,
        email: Optional[str] = None,
        request: Optional[Request] = None,
        success: bool = True,
        failure_reason: Optional[str] = None
    ):
        """認証関連の監査ログ"""
        details = {}
        if failure_reason:
            details["failure_reason"] = failure_reason
        if email and not user:
            details["attempted_email"] = email
        
        self.log_audit(
            action=action,
            user=user,
            resource_type="authentication",
            details=details,
            request=request,
            level=AuditLevel.WARNING if not success else AuditLevel.INFO,
            success=success
        )
    
    def log_resource_access(
        self,
        action: AuditAction,
        user: User,
        resource_type: str,
        resource_id: str,
        request: Optional[Request] = None,
        old_data: Optional[Dict] = None,
        new_data: Optional[Dict] = None
    ):
        """リソースアクセスの監査ログ"""
        details = {}
        if old_data:
            details["old_data"] = old_data
        if new_data:
            details["new_data"] = new_data
        
        self.log_audit(
            action=action,
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request=request
        )
    
    def log_security_event(
        self,
        action: AuditAction,
        user: Optional[User] = None,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.WARNING
    ):
        """セキュリティイベントの監査ログ"""
        self.log_audit(
            action=action,
            user=user,
            resource_type="security",
            details=details,
            request=request,
            level=level,
            success=False
        )

# グローバル監査ログインスタンス
audit_logger = AuditLogger()

def audit_log(
    action: AuditAction,
    resource_type: str,
    get_resource_id: Optional[Callable] = None,
    level: AuditLevel = AuditLevel.INFO
):
    """監査ログデコレータ"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # リクエストとユーザーを取得
            request = None
            current_user = None
            resource_id = None
            
            # 引数からリクエストとユーザーを抽出
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif hasattr(arg, 'id') and hasattr(arg, 'email'):  # User object
                    current_user = arg
            
            # キーワード引数からも確認
            if 'request' in kwargs:
                request = kwargs['request']
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            
            # リソースIDを取得
            if get_resource_id and request:
                try:
                    resource_id = get_resource_id(request, **kwargs)
                except Exception as e:
                    logger.warning("リソースID取得エラー", error=str(e))
            
            try:
                # 関数を実行
                result = await func(*args, **kwargs)
                
                # 成功ログを記録
                audit_logger.log_audit(
                    action=action,
                    user=current_user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request=request,
                    level=level,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # エラーログを記録
                audit_logger.log_audit(
                    action=action,
                    user=current_user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details={"error": str(e), "error_type": type(e).__name__},
                    request=request,
                    level=AuditLevel.ERROR,
                    success=False
                )
                raise
        
        return wrapper
    return decorator

class AuditMiddleware(BaseHTTPMiddleware):
    """監査ログミドルウェア"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # 除外パスをチェック
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = datetime.utcnow()
        response = None
        error = None
        
        try:
            response = await call_next(request)
            await self._log_request(request, response, start_time, True)
            return response
        except Exception as e:
            error = str(e)
            await self._log_request(request, None, start_time, False, error)
            raise
    
    async def _log_request(
        self,
        request: Request,
        response: Optional[Response],
        start_time: datetime,
        success: bool,
        error: Optional[str] = None
    ):
        """リクエストログを記録"""
        try:
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # アクションを決定
            action = self._determine_action(request.method, request.url.path)
            
            details = {
                "method": request.method,
                "path": request.url.path,
                "duration": duration,
                "status_code": response.status_code if response else None,
                "error": error
            }
            
            # ユーザー情報を取得（可能であれば）
            user = getattr(request.state, 'user', None)
            
            audit_logger.log_audit(
                action=action,
                user=user,
                resource_type="http_request",
                details=details,
                request=request,
                level=AuditLevel.ERROR if not success else AuditLevel.INFO,
                success=success
            )
            
        except Exception as e:
            logger.error("リクエストログ記録エラー", error=str(e))
    
    def _determine_action(self, method: str, path: str) -> AuditAction:
        """HTTPメソッドとパスからアクションを決定"""
        # パスベースのアクション判定
        if "/auth/" in path:
            if "login" in path:
                return AuditAction.LOGIN
            elif "logout" in path:
                return AuditAction.LOGOUT
        elif "/users/" in path:
            if method == "POST":
                return AuditAction.USER_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.USER_UPDATE
            elif method == "DELETE":
                return AuditAction.USER_DELETE
        elif "/nodes/" in path:
            if method == "POST":
                return AuditAction.NODE_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.NODE_UPDATE
            elif method == "DELETE":
                return AuditAction.NODE_DELETE
        elif "/blocks/" in path:
            if method == "POST":
                return AuditAction.BLOCK_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.BLOCK_UPDATE
            elif method == "DELETE":
                return AuditAction.BLOCK_DELETE
        elif "/themes/" in path:
            if method == "POST":
                return AuditAction.THEME_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.THEME_UPDATE
            elif method == "DELETE":
                return AuditAction.THEME_DELETE
        
        # デフォルトアクション
        return AuditAction.READ if method == "GET" else AuditAction.SEARCH

def log_user_action(
    action: AuditAction,
    user: User,
    resource_type: str,
    resource_id: str,
    request: Optional[Request] = None,
    **kwargs
):
    """ユーザーアクションログ（簡易版）"""
    details = {k: v for k, v in kwargs.items() if k not in ['old_data', 'new_data']}
    if 'old_data' in kwargs:
        details['old_data'] = kwargs['old_data']
    if 'new_data' in kwargs:
        details['new_data'] = kwargs['new_data']
    
    audit_logger.log_audit(
        action=action,
        user=user,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        request=request
    )

def log_security_violation(
    violation_type: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
    details: Optional[Dict] = None
):
    """セキュリティ違反ログ"""
    audit_logger.log_security_event(
        action=AuditAction.SECURITY_VIOLATION,
        user=user,
        request=request,
        details={"violation_type": violation_type, **(details or {})},
        level=AuditLevel.WARNING
    )

def log_authentication_attempt(
    success: bool,
    user: Optional[User] = None,
    email: Optional[str] = None,
    request: Optional[Request] = None,
    failure_reason: Optional[str] = None
):
    """認証試行ログ"""
    action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
    audit_logger.log_authentication(
        action=action,
        user=user,
        email=email,
        request=request,
        success=success,
        failure_reason=failure_reason
    ) 