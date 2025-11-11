"""
本地模式核心功能模块
"""

import logging
import mimetypes
from typing import Optional

from fastapi import Request, Response

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class LocalHandler:
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
        full_url = f"{self.target_url}/{path.lstrip('/')}"
        if request.url.query:
            full_url += f"?{request.url.query}"

        method = request.method
        logger.info(f"Local mode: {method} request for: {full_url}")

        # 从缓存读取响应
        cached_response = self.cache_manager.get_response(full_url, method)

        if cached_response is None:
            logger.warning(f"Cache not found for: {full_url}")
            return Response(content=f"Cache not found for: {path}", status_code=404)

        # 返回缓存的响应
        content = cached_response["content"]
        headers = cached_response["headers"]
        status_code = cached_response["status_code"]

        # 如果没有 Content-Type,尝试根据路径猜测
        if "content-type" not in headers:
            guessed_type, _ = mimetypes.guess_type(path)
            if guessed_type:
                headers["content-type"] = guessed_type

        logger.info(f"Returning cached response for: {full_url}")

        return Response(content=content, status_code=status_code, headers=headers)
