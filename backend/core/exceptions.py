"""
自定义异常类
"""
from typing import Any, Optional


class SkillsException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Any = None,
        status_code: int = 400
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(SkillsException):
    """资源未找到异常"""

    def __init__(self, resource: str, id: Optional[int] = None):
        details = {"resource": resource}
        if id is not None:
            details["id"] = id
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            details=details,
            status_code=404
        )


class ValidationError(SkillsException):
    """数据验证错误"""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=422
        )


class AuthenticationError(SkillsException):
    """认证错误"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(SkillsException):
    """授权错误"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )


class ConflictError(SkillsException):
    """冲突错误（如重复创建）"""

    def __init__(self, message: str, resource: str = None, field: str = None):
        details = {}
        if resource:
            details["resource"] = resource
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="CONFLICT",
            details=details or None,
            status_code=409
        )


class ExternalServiceError(SkillsException):
    """外部服务错误（如 GitHub/GitLab API 调用失败）"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
            status_code=502
        )
