"""
反代模式核心功能模块
"""

import logging

import httpx
from fastapi import Request, Response

from config import app_config
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ProxyHandler:
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
        target_full_url = f"{self.target_url}/{path.lstrip('/')}"
        if request.url.query:
            target_full_url += f"?{request.url.query}"

        method = request.method
        logger.info(f"Proxying {method} request to: {target_full_url}")

        try:
            # 转发请求到目标服务器
            headers = dict(request.headers)
            # 移除可能导致问题的 headers
            headers.pop("host", None)
            headers.pop("connection", None)

            # 读取请求体
            body = await request.body()

            # 发送请求
            response = await self.client.request(
                method=method, url=target_full_url, headers=headers, content=body
            )

            # 获取响应内容 - 直接转发,不做任何处理
            response_headers = dict(response.headers)
            status_code = response.status_code
            content = response.content
            content_type = response_headers.get("content-type", "")

            logger.debug(f"Response status: {status_code}")
            logger.debug(f"Response content-type: {content_type}")
            logger.debug(f"Response content length: {len(content)}")

            # 处理重定向 Location header
            if "location" in response_headers:
                original_location = response_headers["location"]
                # 如果 Location 是绝对路径或完整URL，需要转换
                if original_location.startswith(self.target_url):
                    # 完整URL，去掉目标服务器部分，保留路径
                    new_location = original_location[len(self.target_url) :]
                    response_headers["location"] = new_location
                    logger.info(
                        f"Rewriting Location header: {original_location} -> {new_location}"
                    )
                elif original_location.startswith(
                    "http://"
                ) or original_location.startswith("https://"):
                    # 其他域名的完整URL，保持不变
                    logger.info(
                        f"Location header points to external URL: {original_location}"
                    )
                else:
                    # 相对路径，保持不变
                    logger.info(f"Location header is relative: {original_location}")

            # 清理响应头,移除可能导致问题的 headers
            headers_to_remove = [
                "content-length",  # 内容长度会自动计算
                "transfer-encoding",  # 避免分块传输问题
                "content-encoding",  # httpx已自动解压,需移除此header避免浏览器二次解压
            ]
            for header in headers_to_remove:
                response_headers.pop(header, None)

            # 缓存响应 (仅 GET 和 POST)
            if method.upper() in ["GET", "POST"]:
                try:
                    self.cache_manager.save_response(
                        url=target_full_url,
                        method=method,
                        content=content,
                        headers=response_headers,
                        status_code=status_code,
                        body=body if method.upper() == "POST" else None,
                    )
                    logger.info(f"Response cached for: {target_full_url}")
                except Exception as e:
                    logger.error(f"缓存保存失败: {e}")

            # 返回响应 (FastAPI 会自动设置正确的 Content-Length)
            # 调试: 打印返回内容的前100个字符
            if logger.isEnabledFor(logging.DEBUG):
                preview = content[:100].decode("utf-8", errors="ignore")
                logger.debug(f"返回内容预览: {preview}...")

            return Response(
                content=content,
                status_code=status_code,
                headers=response_headers,
                media_type=content_type or "application/octet-stream",
            )

        except httpx.TimeoutException:
            logger.error(f"Request timeout: {target_full_url}")
            return Response(content="Request timeout", status_code=504)
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return Response(content=f"Proxy error: {str(e)}", status_code=500)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
