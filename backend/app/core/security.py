from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from typing import Dict, Optional
import hashlib
import hmac
import structlog
from app.core.config import settings
from functools import wraps
from datetime import datetime, timedelta
import os

logger = structlog.get_logger()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

# CSRF保護
class CSRFProtection:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def generate_token(self, user_id: str) -> str:
        """CSRFトークンを生成"""
        timestamp = str(int(time.time()))
        message = f"{user_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key, 
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
        return f"{message}:{signature}"
    
    def verify_token(self, token: str, user_id: str, max_age: int = 3600) -> bool:
        """CSRFトークンを検証"""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            token_user_id, timestamp, signature = parts
            
            # ユーザーIDチェック
            if token_user_id != user_id:
                return False
            
            # タイムスタンプチェック
            token_time = int(timestamp)
            if time.time() - token_time > max_age:
                return False
            
            # 署名検証
            message = f"{token_user_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False

csrf_protection = CSRFProtection(settings.JWT_SECRET_KEY)

# SQLインジェクション対策のためのクエリサニタイザー
class QuerySanitizer:
    # 危険なSQLキーワードとパターン
    DANGEROUS_PATTERNS = [
        # SQLインジェクション攻撃パターン
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(UNION)\s+(ALL\s+)?SELECT)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bxp_\w+|\bsp_\w+)",
        r"(\b(WAITFOR|DELAY)\b)",
        r"(\b(CAST|CONVERT|CHAR|ASCII)\s*\()",
        r"(\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b)",
        r"(\b(BENCHMARK|SLEEP)\s*\()",
        r"(\b(INFORMATION_SCHEMA|MYSQL\.USER|PG_USER)\b)",
        # NoSQLインジェクション対策
        r"(\$where|\$ne|\$gt|\$lt|\$regex)",
        # XSS対策
        r"(<script|<iframe|<object|<embed|javascript:|vbscript:|onload=|onerror=)",
        # パストラバーサル対策
        r"(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
        # 追加のSQLインジェクション対策
        r"(\b(GRANT|REVOKE|TRUNCATE|REPLACE)\b)",
        r"(\b(SHOW|DESCRIBE|EXPLAIN)\b)",
        r"(\b(BACKUP|RESTORE|ATTACH|DETACH)\b)",
        r"(\b(PRAGMA|VACUUM|ANALYZE)\b)",
        r"(\b(BEGIN|COMMIT|ROLLBACK|SAVEPOINT)\b)",
        r"(\b(DECLARE|CURSOR|FETCH|CLOSE)\b)",
        r"(\b(BULK|OPENROWSET|OPENDATASOURCE)\b)",
        # PostgreSQL特有の危険な関数
        r"(\b(pg_\w+|current_\w+|version\(\))\b)",
        # 時間ベース攻撃対策
        r"(\b(pg_sleep|waitfor\s+delay|benchmark)\b)",
        # ファイルシステムアクセス対策
        r"(\b(copy|\\copy|lo_import|lo_export)\b)",
        # 関数呼び出し対策
        r"(\b(system|shell|cmd|exec|eval)\b)",
    ]
    
    # 許可されたSQL演算子（ホワイトリスト）
    ALLOWED_OPERATORS = {
        '=', '!=', '<>', '<', '>', '<=', '>=', 
        'LIKE', 'ILIKE', 'IN', 'NOT IN', 'IS NULL', 'IS NOT NULL',
        'AND', 'OR', 'NOT', 'BETWEEN', 'EXISTS'
    }
    
    # 許可されたSQL関数（ホワイトリスト）
    ALLOWED_FUNCTIONS = {
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
        'UPPER', 'LOWER', 'TRIM', 'LENGTH',
        'COALESCE', 'NULLIF', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
    }
    
    @staticmethod
    def validate_sql_query_structure(query: str) -> bool:
        """SQLクエリの構造を検証（より厳密）"""
        import re
        
        # 基本的な構造チェック
        query_upper = query.upper().strip()
        
        # 許可されたクエリタイプのみ
        allowed_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        if not any(query_upper.startswith(start) for start in allowed_starts):
            return False
        
        # 複数ステートメント禁止
        if ';' in query and not query.strip().endswith(';'):
            return False
        
        # ネストしたクエリの深度制限
        nested_depth = query.count('(') - query.count(')')
        if abs(nested_depth) > 3:  # 最大3レベルまで
            return False
        
        # 危険なパターンチェック
        for pattern in QuerySanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def sanitize_sql_parameter(value: str, param_type: str = "string") -> str:
        """SQLパラメータの型別サニタイズ"""
        if param_type == "uuid":
            if not QuerySanitizer.validate_uuid(value):
                raise ValueError("Invalid UUID format")
            return value
        
        elif param_type == "integer":
            try:
                int_val = int(value)
                if int_val < -2147483648 or int_val > 2147483647:
                    raise ValueError("Integer out of range")
                return str(int_val)
            except ValueError:
                raise ValueError("Invalid integer format")
        
        elif param_type == "email":
            if not QuerySanitizer.validate_email(value):
                raise ValueError("Invalid email format")
            return QuerySanitizer.sanitize_string(value)
        
        elif param_type == "identifier":
            if not QuerySanitizer.validate_sql_identifier(value):
                raise ValueError("Invalid SQL identifier")
            return value
        
        else:  # string type
            return QuerySanitizer.sanitize_string(value)
    
    @staticmethod
    def create_parameterized_query(base_query: str, params: dict) -> tuple:
        """パラメータ化クエリの作成"""
        import re
        
        # プレースホルダーの検証
        placeholders = re.findall(r'\{(\w+)\}', base_query)
        
        # 必要なパラメータがすべて提供されているかチェック
        for placeholder in placeholders:
            if placeholder not in params:
                raise ValueError(f"Missing parameter: {placeholder}")
        
        # パラメータのサニタイズ
        sanitized_params = {}
        for key, value in params.items():
            if isinstance(value, str):
                sanitized_params[key] = QuerySanitizer.sanitize_string(value)
            else:
                sanitized_params[key] = value
        
        # クエリの構築
        try:
            final_query = base_query.format(**sanitized_params)
        except KeyError as e:
            raise ValueError(f"Invalid parameter reference: {e}")
        
        # 最終的なクエリの検証
        if not QuerySanitizer.validate_sql_query_structure(final_query):
            raise ValueError("Invalid query structure detected")
        
        return final_query, sanitized_params
    
    @staticmethod
    def detect_sql_injection_attempt(input_string: str) -> dict:
        """SQLインジェクション試行の詳細検出"""
        import re
        
        detected_patterns = []
        risk_level = "low"
        
        for i, pattern in enumerate(QuerySanitizer.DANGEROUS_PATTERNS):
            matches = re.findall(pattern, input_string, re.IGNORECASE)
            if matches:
                detected_patterns.append({
                    "pattern_id": i,
                    "pattern": pattern,
                    "matches": matches,
                    "description": QuerySanitizer._get_pattern_description(i)
                })
        
        # リスクレベルの判定
        if len(detected_patterns) > 3:
            risk_level = "critical"
        elif len(detected_patterns) > 1:
            risk_level = "high"
        elif len(detected_patterns) == 1:
            risk_level = "medium"
        
        return {
            "is_suspicious": len(detected_patterns) > 0,
            "risk_level": risk_level,
            "detected_patterns": detected_patterns,
            "input_length": len(input_string),
            "sanitized_input": QuerySanitizer.sanitize_string(input_string)
        }
    
    @staticmethod
    def _get_pattern_description(pattern_id: int) -> str:
        """パターンIDに対応する説明を取得"""
        descriptions = [
            "SQL DML commands detected",
            "Boolean-based injection pattern",
            "UNION-based injection pattern", 
            "SQL comment injection",
            "Extended stored procedures",
            "Time-based injection",
            "Type conversion functions",
            "File operation functions",
            "Benchmark/sleep functions",
            "Information schema access",
            "NoSQL injection patterns",
            "XSS patterns",
            "Path traversal patterns",
            "SQL DDL commands",
            "SQL metadata commands",
            "Backup/restore commands",
            "Database maintenance commands",
            "Transaction control commands",
            "Cursor operations",
            "Bulk operations",
            "PostgreSQL system functions",
            "Time-based attack functions",
            "File system access",
            "System command execution"
        ]
        return descriptions[pattern_id] if pattern_id < len(descriptions) else "Unknown pattern"
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """文字列をサニタイズ"""
        if not isinstance(value, str):
            return str(value)
        
        # 長さ制限
        if len(value) > max_length:
            value = value[:max_length]
        
        # 危険なパターンをチェック
        import re
        for pattern in QuerySanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning("Dangerous pattern detected in input", pattern=pattern, input=value[:100])
                # 危険なパターンを削除
                value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        # HTMLエンティティエスケープ
        import html
        value = html.escape(value)
        
        # 制御文字を削除
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        return value.strip()
    
    @staticmethod
    def sanitize_json(data: dict) -> dict:
        """JSONデータを再帰的にサニタイズ"""
        if isinstance(data, dict):
            return {key: QuerySanitizer.sanitize_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [QuerySanitizer.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return QuerySanitizer.sanitize_string(data)
        else:
            return data
    
    @staticmethod
    def validate_uuid(value: str) -> bool:
        """UUIDの形式を検証"""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """メールアドレスの形式を検証"""
        import re
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(email))
    
    @staticmethod
    def validate_sql_identifier(identifier: str) -> bool:
        """SQLの識別子（テーブル名、カラム名など）を検証"""
        import re
        # 英数字とアンダースコアのみ許可、数字で始まらない
        pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        return bool(pattern.match(identifier)) and len(identifier) <= 63
    
    @staticmethod
    def escape_like_pattern(pattern: str) -> str:
        """LIKE句のパターンをエスケープ"""
        # %と_をエスケープ
        return pattern.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

query_sanitizer = QuerySanitizer()

# IP制限機能
class IPWhitelist:
    def __init__(self):
        self.whitelist: Dict[str, bool] = {}
        self.blacklist: Dict[str, bool] = {}
    
    def add_to_whitelist(self, ip: str):
        """IPをホワイトリストに追加"""
        self.whitelist[ip] = True
    
    def add_to_blacklist(self, ip: str):
        """IPをブラックリストに追加"""
        self.blacklist[ip] = True
    
    def is_allowed(self, ip: str) -> bool:
        """IPが許可されているかチェック"""
        if ip in self.blacklist:
            return False
        
        # ホワイトリストが設定されている場合は、ホワイトリストのみ許可
        if self.whitelist:
            return ip in self.whitelist
        
        return True

ip_whitelist = IPWhitelist()

# ブルートフォース攻撃対策
class BruteForceProtection:
    def __init__(self, max_attempts: int = 5, lockout_time: int = 300):
        self.max_attempts = max_attempts
        self.lockout_time = lockout_time
        self.attempts: Dict[str, Dict] = {}
    
    def record_attempt(self, identifier: str, success: bool = False):
        """ログイン試行を記録"""
        now = time.time()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = {
                'count': 0,
                'last_attempt': now,
                'locked_until': 0
            }
        
        attempt_data = self.attempts[identifier]
        
        if success:
            # 成功時はカウントをリセット
            attempt_data['count'] = 0
            attempt_data['locked_until'] = 0
        else:
            # 失敗時はカウントを増加
            attempt_data['count'] += 1
            attempt_data['last_attempt'] = now
            
            if attempt_data['count'] >= self.max_attempts:
                attempt_data['locked_until'] = now + self.lockout_time
    
    def is_blocked(self, identifier: str) -> bool:
        """アカウントがロックされているかチェック"""
        if identifier not in self.attempts:
            return False
        
        attempt_data = self.attempts[identifier]
        return time.time() < attempt_data['locked_until']
    
    def get_remaining_lockout_time(self, identifier: str) -> int:
        """残りロック時間を取得"""
        if identifier not in self.attempts:
            return 0
        
        attempt_data = self.attempts[identifier]
        remaining = attempt_data['locked_until'] - time.time()
        return max(0, int(remaining))

brute_force_protection = BruteForceProtection()

# セキュリティミドルウェアクラス
class SecurityMiddleware:
    """セキュリティミドルウェア（環境別設定対応）"""
    
    def __init__(self, app, security_headers: dict = None, environment: str = "development"):
        self.app = app
        self.security_headers = security_headers or SECURITY_HEADERS
        self.environment = environment
        self.ip_whitelist = set(os.getenv("IP_WHITELIST", "").split(",")) if os.getenv("IP_WHITELIST") else set()
        self.ip_blacklist = set(os.getenv("IP_BLACKLIST", "").split(",")) if os.getenv("IP_BLACKLIST") else set()
        
        # 環境別の追加設定
        if environment == "production":
            # 本番環境では追加のIP制限
            self.enable_strict_ip_validation = True
            self.log_all_requests = True
        else:
            self.enable_strict_ip_validation = False
            self.log_all_requests = False
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # リクエスト情報の取得
        client_ip = self._get_client_ip(scope)
        user_agent = self._get_user_agent(scope)
        request_path = scope.get("path", "")
        
        # IP制限チェック
        if not self._check_ip_access(client_ip):
            await self._send_forbidden_response(send, f"Access denied for IP: {client_ip}")
            return
        
        # 疑わしいUser-Agentのチェック
        if self._is_suspicious_user_agent(user_agent):
            logger.warning("Suspicious user agent detected", 
                         client_ip=client_ip, 
                         user_agent=user_agent,
                         path=request_path)
            
            if self.environment == "production":
                await self._send_forbidden_response(send, "Suspicious request detected")
                return
        
        # レスポンスの処理
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # セキュリティヘッダーを追加
                headers = list(message.get("headers", []))
                
                for name, value in self.security_headers.items():
                    headers.append([name.encode(), value.encode()])
                
                # 環境別の追加ヘッダー
                if self.environment == "production":
                    headers.append([b"X-Environment", b"production"])
                    headers.append([b"X-Security-Level", b"strict"])
                elif self.environment == "development":
                    headers.append([b"X-Environment", b"development"])
                    headers.append([b"X-Security-Level", b"relaxed"])
                
                message["headers"] = headers
            
            await send(message)
        
        # ログ記録（本番環境または設定有効時）
        if self.log_all_requests or self.environment == "production":
            logger.info("Security middleware processing request",
                       client_ip=client_ip,
                       user_agent=user_agent,
                       path=request_path,
                       environment=self.environment)
        
        await self.app(scope, receive, send_wrapper)
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """疑わしいUser-Agentを検出"""
        if not user_agent:
            return True
        
        suspicious_patterns = [
            r"sqlmap",
            r"nikto", 
            r"nmap",
            r"masscan",
            r"zap",
            r"burp",
            r"scanner",
            r"bot.*crawler",
            r"python-requests",
            r"curl",
            r"wget",
            r"libwww",
            r"<script",
            r"javascript:",
            r"vbscript:",
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        
        return False
    
    def _get_user_agent(self, scope) -> str:
        """User-Agentヘッダーを取得"""
        headers = dict(scope.get("headers", []))
        return headers.get(b"user-agent", b"").decode("utf-8", errors="ignore")
    
    def _get_client_ip(self, scope) -> str:
        """クライアントIPアドレスを取得"""
        headers = dict(scope.get("headers", []))
        
        # プロキシ経由の場合のIPアドレス取得
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            # 最初のIPアドレスを取得（カンマ区切りの場合）
            ip = forwarded_for.decode("utf-8").split(",")[0].strip()
            return ip
        
        real_ip = headers.get(b"x-real-ip")
        if real_ip:
            return real_ip.decode("utf-8")
        
        # 直接接続の場合
        client = scope.get("client")
        if client:
            return client[0]
        
        return "unknown"
    
    def _check_ip_access(self, client_ip: str) -> bool:
        """IP制限チェック"""
        # 開発環境では制限なし
        if self.environment == "development":
            return True
        
        # ローカルIPは常に許可
        if client_ip in ["127.0.0.1", "::1", "localhost", "unknown"]:
            return True
        
        # 本番環境でのIP制限ロジックをここに実装
        # 現在は全て許可
        return True
    
    async def _send_forbidden_response(self, send, message: str):
        """403 Forbiddenレスポンスを送信"""
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(message)).encode()],
            ] + [[name.encode(), value.encode()] for name, value in self.security_headers.items()]
        })
        await send({
            "type": "http.response.body",
            "body": f'{{"error": "{message}"}}'.encode()
        })

# 入力値検証デコレータ
def validate_input(validation_rules: dict):
    """入力値検証デコレータ
    
    Args:
        validation_rules: {field_name: validation_function} の辞書
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # リクエストボディを取得
            for arg in args:
                if hasattr(arg, 'dict'):  # Pydanticモデル
                    data = arg.dict()
                    for field, validator in validation_rules.items():
                        if field in data:
                            if not validator(data[field]):
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Invalid {field} format"
                                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 

# セキュリティヘッダー設定
SECURITY_HEADERS = {
    # XSS対策
    "X-XSS-Protection": "1; mode=block",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    
    # HTTPS強制
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    
    # コンテンツセキュリティポリシー（厳格版）
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none';"
    ),
    
    # 権限ポリシー
    "Permissions-Policy": (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "speaker=(), "
        "vibrate=(), "
        "fullscreen=(self), "
        "sync-xhr=()"
    ),
    
    # リファラーポリシー
    "Referrer-Policy": "strict-origin-when-cross-origin",
    
    # クロスオリジンポリシー
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    
    # キャッシュ制御
    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    
    # サーバー情報隠蔽
    "Server": "KAGRA-API",
    "X-Powered-By": "",
}

# 環境別セキュリティヘッダー設定
def get_environment_security_headers(environment: str) -> dict:
    """環境に応じたセキュリティヘッダーを取得"""
    base_headers = SECURITY_HEADERS.copy()
    
    if environment == "development":
        # 開発環境では一部制限を緩和
        base_headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "connect-src 'self' http://localhost:* ws://localhost:* "
            "https://api.supabase.co wss://realtime.supabase.co; "
            "img-src 'self' data: https: http:; "
            "font-src 'self' https: data:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
            "frame-ancestors 'none';"
        )
        
        # 開発環境では HSTS を無効化
        base_headers["Strict-Transport-Security"] = "max-age=0"
        
        # クロスオリジンポリシーを緩和
        base_headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
        base_headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        
    elif environment == "staging":
        # ステージング環境では本番に近い設定だが一部緩和
        base_headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https:; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'none';"
        )
        
        # ステージング環境では短めのHSTS
        base_headers["Strict-Transport-Security"] = "max-age=86400; includeSubDomains"
        
    elif environment == "production":
        # 本番環境では最も厳格な設定
        base_headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests;"
        )
        
        # 本番環境では追加のセキュリティヘッダー
        base_headers.update({
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-Download-Options": "noopen",
            "X-DNS-Prefetch-Control": "off",
            "Expect-CT": "max-age=86400, enforce",
            "Feature-Policy": (
                "geolocation 'none'; "
                "microphone 'none'; "
                "camera 'none'; "
                "payment 'none'; "
                "usb 'none';"
            )
        })
    
    return base_headers

# セキュリティヘッダー検証機能
class SecurityHeaderValidator:
    """セキュリティヘッダーの検証クラス"""
    
    @staticmethod
    def validate_csp(csp_header: str) -> dict:
        """CSPヘッダーの検証"""
        issues = []
        recommendations = []
        
        # 危険な設定をチェック
        if "'unsafe-eval'" in csp_header:
            issues.append("'unsafe-eval' is present in CSP - high security risk")
        
        if "'unsafe-inline'" in csp_header:
            issues.append("'unsafe-inline' is present in CSP - medium security risk")
        
        if "data:" in csp_header and "img-src" not in csp_header:
            issues.append("data: scheme allowed globally - potential security risk")
        
        # 推奨設定をチェック
        if "frame-ancestors" not in csp_header:
            recommendations.append("Add 'frame-ancestors' directive to prevent clickjacking")
        
        if "base-uri" not in csp_header:
            recommendations.append("Add 'base-uri' directive to prevent base tag injection")
        
        if "form-action" not in csp_header:
            recommendations.append("Add 'form-action' directive to control form submissions")
        
        return {
            "is_secure": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "score": max(0, 100 - len(issues) * 20 - len(recommendations) * 5)
        }
    
    @staticmethod
    def validate_hsts(hsts_header: str) -> dict:
        """HSTSヘッダーの検証"""
        issues = []
        recommendations = []
        
        if not hsts_header:
            issues.append("HSTS header is missing")
            return {"is_secure": False, "issues": issues, "recommendations": [], "score": 0}
        
        # max-ageの確認
        if "max-age=" not in hsts_header:
            issues.append("HSTS max-age directive is missing")
        else:
            import re
            max_age_match = re.search(r'max-age=(\d+)', hsts_header)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                if max_age < 31536000:  # 1年未満
                    recommendations.append("HSTS max-age should be at least 1 year (31536000 seconds)")
        
        # includeSubDomainsの確認
        if "includeSubDomains" not in hsts_header:
            recommendations.append("Consider adding 'includeSubDomains' to HSTS")
        
        # preloadの確認
        if "preload" not in hsts_header:
            recommendations.append("Consider adding 'preload' to HSTS for enhanced security")
        
        return {
            "is_secure": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "score": max(0, 100 - len(issues) * 30 - len(recommendations) * 10)
        }
    
    @staticmethod
    def validate_all_headers(headers: dict) -> dict:
        """すべてのセキュリティヘッダーを検証"""
        results = {}
        overall_score = 0
        total_headers = 0
        
        # CSP検証
        if "Content-Security-Policy" in headers:
            results["csp"] = SecurityHeaderValidator.validate_csp(headers["Content-Security-Policy"])
            overall_score += results["csp"]["score"]
            total_headers += 1
        
        # HSTS検証
        if "Strict-Transport-Security" in headers:
            results["hsts"] = SecurityHeaderValidator.validate_hsts(headers["Strict-Transport-Security"])
            overall_score += results["hsts"]["score"]
            total_headers += 1
        
        # 必須ヘッダーの存在確認
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Referrer-Policy"
        ]
        
        missing_headers = []
        for header in required_headers:
            if header not in headers:
                missing_headers.append(header)
            else:
                total_headers += 1
                overall_score += 80  # 基本点
        
        if missing_headers:
            results["missing_headers"] = {
                "headers": missing_headers,
                "impact": "Medium security risk"
            }
        
        # 全体スコア計算
        final_score = overall_score / max(total_headers, 1) if total_headers > 0 else 0
        
        return {
            "overall_score": round(final_score, 2),
            "security_level": SecurityHeaderValidator._get_security_level(final_score),
            "results": results,
            "total_headers_checked": total_headers
        }
    
    @staticmethod
    def _get_security_level(score: float) -> str:
        """スコアに基づくセキュリティレベルを取得"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Poor"
        else:
            return "Critical"

security_header_validator = SecurityHeaderValidator()

# セキュリティ機能の統合テスト用ヘルパー
class SecurityTester:
    """セキュリティ機能のテスト用クラス"""
    
    @staticmethod
    def test_sql_injection_patterns():
        """SQLインジェクションパターンのテスト"""
        test_cases = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
            "admin'/*",
            "1; EXEC xp_cmdshell('dir')",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "$where: {$ne: null}"
        ]
        
        results = []
        for test_case in test_cases:
            sanitized = query_sanitizer.sanitize_string(test_case)
            is_safe = test_case != sanitized
            results.append({
                "input": test_case,
                "output": sanitized,
                "blocked": is_safe
            })
        
        return results
    
    @staticmethod
    def test_validation_functions():
        """バリデーション関数のテスト"""
        tests = {
            "uuid": [
                ("550e8400-e29b-41d4-a716-446655440000", True),
                ("invalid-uuid", False),
                ("", False)
            ],
            "email": [
                ("test@example.com", True),
                ("invalid-email", False),
                ("test@", False)
            ],
            "sql_identifier": [
                ("valid_table_name", True),
                ("123invalid", False),
                ("table-name", False),
                ("very_long_table_name_that_exceeds_the_limit_of_63_characters_and_should_fail", False)
            ]
        }
        
        results = {}
        for test_type, test_cases in tests.items():
            results[test_type] = []
            for input_val, expected in test_cases:
                if test_type == "uuid":
                    actual = query_sanitizer.validate_uuid(input_val)
                elif test_type == "email":
                    actual = query_sanitizer.validate_email(input_val)
                elif test_type == "sql_identifier":
                    actual = query_sanitizer.validate_sql_identifier(input_val)
                
                results[test_type].append({
                    "input": input_val,
                    "expected": expected,
                    "actual": actual,
                    "passed": actual == expected
                })
        
        return results

security_tester = SecurityTester() 