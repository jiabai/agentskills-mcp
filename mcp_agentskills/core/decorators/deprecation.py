from functools import wraps
from typing import Callable, Optional

from fastapi import Response


def deprecated(
    sunset_date: Optional[str] = None,
    alternative: Optional[str] = None,
) -> Callable:
    """
    标记端点为已弃用的装饰器

    注意：此装饰器需要配合 FastAPI 的 Response 依赖注入使用。
    路由函数必须在参数中声明 `response: Response` 才能正确设置响应头。

    Args:
        sunset_date: 端点完全移除的日期（ISO 8601格式，如 "2026-12-31"）
        alternative: 替代端点的路径

    Usage:
        @router.get("/legacy/endpoint")
        @deprecated(sunset_date="2026-12-31", alternative="/api/v1/new/endpoint")
        async def legacy_endpoint(response: Response):
            '''已弃用的端点'''
            return {"message": "This endpoint is deprecated"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, response: Optional[Response] = None, **kwargs):
            if response is not None and isinstance(response, Response):
                response.headers["Deprecation"] = "true"
                if sunset_date:
                    response.headers["Sunset"] = sunset_date
                if alternative:
                    response.headers["Link"] = f'<{alternative}>; rel="successor-version"'

            return await func(*args, response=response, **kwargs)

        wrapper._deprecated = True
        wrapper._sunset_date = sunset_date
        wrapper._alternative = alternative

        return wrapper

    return decorator


def get_deprecation_metadata(func: Callable) -> dict:
    """
    获取函数的弃用元数据，用于文档生成

    Returns:
        dict: 包含 deprecated, sunset_date, alternative 的字典
    """
    return {
        "deprecated": getattr(func, "_deprecated", False),
        "sunset_date": getattr(func, "_sunset_date", None),
        "alternative": getattr(func, "_alternative", None),
    }
