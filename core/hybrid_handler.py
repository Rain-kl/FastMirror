"""
半代理模式核心功能模块
优先使用本地缓存，不存在时则代理并缓存
"""

import logging

from fastapi import Request, Response

from .cache_manager import CacheManager
from .local_handler import LocalHandler
from .proxy_handler import ProxyHandler

logger = logging.getLogger(__name__)


class HybridHandler:
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
        full_url = f"{self.target_url}/{path.lstrip('/')}"
        if request.url.query:
            full_url += f"?{request.url.query}"

        method = request.method
        logger.info(f"Hybrid mode: {method} request for: {full_url}")

        # 读取请求体（POST 请求需要用于缓存查找）
        body = await request.body() if method.upper() == "POST" else None

        # 检查缓存是否存在
        if self.cache_manager.has_cache(full_url, method, body):
            logger.info(f"Cache hit, using local cache for: {full_url}")
            # 从缓存读取
            cached_response = self.cache_manager.get_response(full_url, method, body)
            
            if cached_response:
                content = cached_response["content"]
                headers = cached_response["headers"]
                status_code = cached_response["status_code"]
                
                # 如果没有 Content-Type，尝试根据路径猜测
                if "content-type" not in headers:
                    import mimetypes
                    guessed_type, _ = mimetypes.guess_type(path)
                    if guessed_type:
                        headers["content-type"] = guessed_type
                
                logger.info(f"Returning cached response for: {full_url}")
                return Response(content=content, status_code=status_code, headers=headers)

        # 缓存不存在，使用代理模式
        logger.info(f"Cache miss, proxying request to: {full_url}")
        # 注意：需要重新创建 Request 对象，因为 body 已经被读取
        # 但 ProxyHandler 会再次读取，所以这里需要特殊处理
        return await self.proxy_handler.handle_request(request, path)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.proxy_handler.close()
