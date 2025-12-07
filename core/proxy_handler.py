"""
反代模式核心功能模块
"""

import logging

import httpx
from fastapi import Request, Response

from config import app_config
from utils import HttpUtil, constants
from .cache_manager import CacheManager
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)


class ProxyHandler(BaseHandler):
    """反代请求处理器"""

    def __init__(self, target_url: str, cache_manager: CacheManager):
        """
        初始化反代处理器

        Args:
            target_url: 目标服务器 URL
            cache_manager: 缓存管理器实例
        """
        self.target_url = target_url.rstrip("/")
        self.cache_manager = cache_manager
        self.client = httpx.AsyncClient(
            timeout=app_config.request_timeout, follow_redirects=False
        )

    async def handle_request(self, request: Request, path: str) -> Response:
        """
        处理反代请求

        Args:
            request: FastAPI 请求对象
            path: 请求路径

        Returns:
            FastAPI 响应对象
        """
        # 构建目标 URL
        target_full_url = self.build_full_url(
            self.target_url, path, str(request.url.query) if request.url.query else None
        )
        method = request.method
        self.log_request(method, target_full_url, "Proxying")

        try:
            # 清理请求头
            headers = HttpUtil.clean_proxy_request_headers(dict(request.headers))

            # 读取请求体
            body = await self.read_request_body(request)

            # 发送请求
            response = await self.client.request(
                method=method, url=target_full_url, headers=headers, content=body
            )

            # 获取响应内容
            response_headers = dict(response.headers)
            status_code = response.status_code
            content = response.content

            logger.debug(f"Response status: {status_code}")
            logger.debug(f"Response content-type: {response_headers.get('content-type', '')}")
            logger.debug(f"Response content length: {len(content)}")

            # 处理重定向 Location header
            if "location" in response_headers:
                original_location = response_headers["location"]
                new_location, modified = HttpUtil.rewrite_location_header(
                    original_location, self.target_url
                )
                if modified:
                    response_headers["location"] = new_location
                    logger.info(f"Rewriting Location: {original_location} -> {new_location}")

            # 清理响应头
            response_headers = HttpUtil.clean_response_headers(response_headers)

            # 缓存响应 (仅 GET 和 POST)
            if method.upper() in constants.CACHEABLE_METHODS:
                try:
                    self.cache_manager.save_response(
                        url=target_full_url,
                        method=method,
                        content=content,
                        headers=response_headers,
                        status_code=status_code,
                        body=body if method.upper() == constants.HTTP_METHOD_POST else None,
                    )
                    logger.info(f"Response cached for: {target_full_url}")
                except Exception as e:
                    logger.error(f"缓存保存失败: {e}")

            # 调试: 打印返回内容预览
            if logger.isEnabledFor(logging.DEBUG):
                preview = content[: constants.LOG_PREVIEW_LENGTH].decode(
                    constants.ENCODING_UTF8, errors="ignore"
                )
                logger.debug(f"返回内容预览: {preview}...")

            return self.build_response(content, status_code, response_headers, path)

        except httpx.TimeoutException:
            logger.error(f"Request timeout: {target_full_url}")
            return Response(
                content="Request timeout",
                status_code=constants.HTTP_STATUS_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return Response(
                content=f"Proxy error: {str(e)}",
                status_code=constants.HTTP_STATUS_INTERNAL_ERROR,
            )

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
