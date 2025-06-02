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
            
            # データベースに記録
            supabase = self._get_supabase()
            response = supabase.table('audit_logs').insert(audit_data).execute()
            
            if not response.data:
                logger.error("監査ログの記録に失敗", action=action.value)
            
            # 構造化ログにも出力
            logger.info(
                "Audit log recorded",
                action=action.value,
                user_id=user.id if user else None,
                resource_type=resource_type,
                resource_id=resource_id,
                level=level.value,
                success=success
            )
            
        except Exception as e:
            logger.error("監査ログ記録エラー", error=str(e), action=action.value)
    
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

# 監査ログデコレータ
def audit_log(
    action: AuditAction,
    resource_type: str,
    get_resource_id: Optional[Callable] = None,
    level: AuditLevel = AuditLevel.INFO
):
    """監査ログデコレータ
    
    Args:
        action: 監査アクション
        resource_type: リソースタイプ
        get_resource_id: リソースIDを取得する関数（引数から動的に取得）
        level: ログレベル
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            user = None
            resource_id = None
            success = True
            error_details = None
            
            # 引数からrequestとuserを取得
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif hasattr(arg, 'id') and hasattr(arg, 'email'):
                    user = arg
            
            # キーワード引数からも取得
            if 'request' in kwargs:
                request = kwargs['request']
            if 'current_user' in kwargs:
                user = kwargs['current_user']
            
            # リソースIDを動的に取得
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception as e:
                    resource_id = None
            
            try:
                # 元の関数を実行
                result = await func(*args, **kwargs)
                
                # 成功時の監査ログ
                audit_logger.log_audit(
                    action=action,
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request=request,
                    level=level,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # エラー時の監査ログ
                success = False
                error_details = {"error": str(e), "error_type": type(e).__name__}
                
                audit_logger.log_audit(
                    action=action,
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=error_details,
                    request=request,
                    level=AuditLevel.ERROR,
                    success=False
                )
                
                # エラーを再発生
                raise
        
        return wrapper
    return decorator

# 自動監査ミドルウェア
class AuditMiddleware(BaseHTTPMiddleware):
    """全リクエストを自動的に監査ログに記録するミドルウェア"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # 除外パスをチェック
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = datetime.utcnow()
        
        try:
            # リクエストを処理
            response = await call_next(request)
            
            # 成功時の監査ログ
            await self._log_request(request, response, start_time, True)
            
            return response
            
        except Exception as e:
            # エラー時の監査ログ
            await self._log_request(request, None, start_time, False, str(e))
            raise
    
    async def _log_request(
        self,
        request: Request,
        response: Optional[Response],
        start_time: datetime,
        success: bool,
        error: Optional[str] = None
    ):
        """リクエストを監査ログに記録"""
        try:
            # 処理時間を計算
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # リクエスト詳細を構築
            details = {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "duration_seconds": duration,
                "status_code": response.status_code if response else None
            }
            
            if error:
                details["error"] = error
            
            # アクションを決定
            action = self._determine_action(request.method, request.url.path)
            
            # ユーザー情報を取得（可能であれば）
            user = getattr(request.state, 'user', None)
            
            # 監査ログを記録
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
            logger.error("監査ミドルウェアエラー", error=str(e))
    
    def _determine_action(self, method: str, path: str) -> AuditAction:
        """HTTPメソッドとパスからアクションを決定"""
        if "auth" in path:
            if method == "POST" and "login" in path:
                return AuditAction.LOGIN
            elif method == "POST" and "logout" in path:
                return AuditAction.LOGOUT
        elif "theme" in path:
            if method == "POST":
                return AuditAction.THEME_CREATE
            elif method == "PUT":
                return AuditAction.THEME_UPDATE
            elif method == "DELETE":
                return AuditAction.THEME_DELETE
        elif "node" in path:
            if method == "POST":
                return AuditAction.NODE_CREATE
            elif method == "PUT":
                return AuditAction.NODE_UPDATE
            elif method == "DELETE":
                return AuditAction.NODE_DELETE
        elif "block" in path:
            if method == "POST":
                return AuditAction.BLOCK_CREATE
            elif method == "PUT":
                return AuditAction.BLOCK_UPDATE
            elif method == "DELETE":
                return AuditAction.BLOCK_DELETE
        elif "user" in path:
            if method == "POST":
                return AuditAction.USER_CREATE
            elif method == "PUT":
                return AuditAction.USER_UPDATE
            elif method == "DELETE":
                return AuditAction.USER_DELETE
        
        # デフォルトアクション
        if method == "GET":
            return AuditAction.READ
        else:
            return AuditAction.READ

# 便利な関数
def log_user_action(
    action: AuditAction,
    user: User,
    resource_type: str,
    resource_id: str,
    request: Optional[Request] = None,
    **kwargs
):
    """ユーザーアクションをログ記録"""
    audit_logger.log_resource_access(
        action=action,
        user=user,
        resource_type=resource_type,
        resource_id=resource_id,
        request=request,
        **kwargs
    )

def log_security_violation(
    violation_type: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
    details: Optional[Dict] = None
):
    """セキュリティ違反をログ記録"""
    audit_details = {"violation_type": violation_type}
    if details:
        audit_details.update(details)
    
    audit_logger.log_security_event(
        action=AuditAction.SECURITY_VIOLATION,
        user=user,
        request=request,
        details=audit_details,
        level=AuditLevel.ERROR
    )

def log_authentication_attempt(
    success: bool,
    user: Optional[User] = None,
    email: Optional[str] = None,
    request: Optional[Request] = None,
    failure_reason: Optional[str] = None
):
    """認証試行をログ記録"""
    action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
    audit_logger.log_authentication(
        action=action,
        user=user,
        email=email,
        request=request,
        success=success,
        failure_reason=failure_reason
    ) 