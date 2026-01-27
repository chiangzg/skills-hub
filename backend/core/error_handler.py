"""
统一错误处理中间件
"""
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import SkillsException
from core.logger import logger


async def skills_exception_handler(
    request: Request,
    exc: SkillsException
) -> JSONResponse:
    """自定义异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url.path),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Pydantic 验证错误处理"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": errors,
                "path": str(request.url.path),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "path": str(request.url.path),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """未捕获异常处理"""
    logger.error(
        f"Unhandled exception on {request.url.path}: {exc}",
        exc_info=True,
        extra={"path": str(request.url.path), "method": request.method}
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "path": str(request.url.path),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
