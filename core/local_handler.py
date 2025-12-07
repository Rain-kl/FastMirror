"""
本地模式核心功能模块
"""

import logging
from typing import Optional

from fastapi import Request, Response

from utils import constants
from .cache_manager import CacheManager
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class LocalHandler(BaseHandler):
    """本地模式请求处理器"""

    def __init__(self, cache_manager: CacheManager, target_url: Optional[str] = None):
        """
        初始化本地处理器

        Args:
            cache_manager: 缓存管理器实例
            target_url: 目标服务器 URL (用于构建完整的缓存 URL)
        """
        self.cache_manager = cache_manager
        self.target_url = target_url.rstrip("/") if target_url else "http://localhost"

    async def handle_request(self, request: Request, path: str) -> Response:
        """
        处理本地模式请求

        Args:
            request: FastAPI 请求对象
            path: 请求路径

        Returns:
            FastAPI 响应对象
        """
        # 构建完整 URL (用于查找缓存)
        full_url = self.build_full_url(
            self.target_url, path, str(request.url.query) if request.url.query else None
        )
        method = request.method
        self.log_request(method, full_url, "Local mode")

        # 读取请求体（POST 请求需要）
        body = (
            await self.read_request_body(request)
            if method.upper() == constants.HTTP_METHOD_POST
            else None
        )

        # 从缓存读取响应
        cached_response = self.cache_manager.get_response(full_url, method, body)

        if cached_response is None:
            logger.warning(f"Cache not found for: {full_url}")
            return Response(
                content=f"Cache not found for: {path}",
                status_code=constants.HTTP_STATUS_NOT_FOUND,
            )

        # 返回缓存的响应
        logger.info(f"Returning cached response for: {full_url}")
        return self.build_response(
            content=cached_response["content"],
            status_code=cached_response["status_code"],
            headers=cached_response["headers"],
            path=path,
        )
