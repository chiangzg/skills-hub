"""
安全中间件：安全响应头、速率限制
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # 移除服务器信息
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = datetime.now()

        # 记录请求
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )

        response = await call_next(request)

        # 记录响应时间和状态
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Response: {response.status_code} ({process_time:.3f}s)",
            extra={
                "status_code": response.status_code,
                "process_time": process_time
            }
        )

        return response


from datetime import datetime


# 简单的内存速率限制器
class RateLimiter:
    """内存速率限制器"""

    def __init__(self):
        self.requests = {}  # {key: [(timestamp, count)]}

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        检查是否允许请求

        Args:
            key: 限制键（如 IP 地址）
            limit: 时间窗口内允许的最大请求数
            window: 时间窗口（秒）
        """
        now = datetime.now().timestamp()

        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [
                (ts, cnt) for ts, cnt in self.requests[key]
                if now - ts < window
            ]
        else:
            self.requests[key] = []

        # 统计当前窗口内的请求数
        count = sum(cnt for ts, cnt in self.requests[key])

        if count >= limit:
            return False

        # 记录本次请求
        self.requests[key].append((now, 1))
        return True


# 全局限流器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    # 路径配置：{路径: (限制次数, 时间窗口秒数)}
    limits = {
        "/api/auth/login": (5, 60),  # 登录：5次/分钟
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 检查是否需要限流
        for limit_path, (limit, window) in self.limits.items():
            if path.startswith(limit_path):
                # 使用客户端 IP 作为限流键
                client_ip = request.client.host if request.client else "unknown"
                key = f"{client_ip}:{path}"

                if not rate_limiter.is_allowed(key, limit, window):
                    from fastapi import status
                    from fastapi.responses import JSONResponse

                    logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": "Too many requests. Please try again later."
                            }
                        }
                    )
                break

        return await call_next(request)
