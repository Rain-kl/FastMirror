"""
半代理模式核心功能模块
优先使用本地缓存，不存在时则代理并缓存
"""

import logging

from fastapi import Request, Response

from utils import constants
from .cache_manager import CacheManager
from .local_handler import LocalHandler
from .proxy_handler import ProxyHandler
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class HybridHandler(BaseHandler):
    """半代理模式请求处理器"""

    def __init__(self, target_url: str, cache_manager: CacheManager):
        """
        初始化半代理处理器

        Args:
            target_url: 目标服务器 URL
            cache_manager: 缓存管理器实例
        """
        self.target_url = target_url.rstrip("/")
        self.cache_manager = cache_manager
        
        # 初始化本地处理器和代理处理器
        self.local_handler = LocalHandler(cache_manager, target_url)
        self.proxy_handler = ProxyHandler(target_url, cache_manager)

    async def handle_request(self, request: Request, path: str) -> Response:
        """
        处理半代理模式请求
        优先从缓存读取，不存在则代理并缓存

        Args:
            request: FastAPI 请求对象
            path: 请求路径

        Returns:
            FastAPI 响应对象
        """
        # 构建完整 URL
        full_url = self.build_full_url(
            self.target_url, path, str(request.url.query) if request.url.query else None
        )
        method = request.method
        self.log_request(method, full_url, "Hybrid mode")

        # 读取请求体（POST 请求需要用于缓存查找）
        body = (
            await self.read_request_body(request)
            if method.upper() == constants.HTTP_METHOD_POST
            else None
        )

        # 检查缓存是否存在
        if self.cache_manager.has_cache(full_url, method, body):
            logger.info(f"Cache hit, using local cache for: {full_url}")
            # 从缓存读取
            cached_response = self.cache_manager.get_response(full_url, method, body)
            
            if cached_response:
                logger.info(f"Returning cached response for: {full_url}")
                return self.build_response(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response["headers"],
                    path=path,
                )

        # 缓存不存在，使用代理模式
        logger.info(f"Cache miss, proxying request to: {full_url}")
        return await self.proxy_handler.handle_request(request, path)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.proxy_handler.close()
