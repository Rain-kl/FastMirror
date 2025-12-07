"""
Handler 基类，提供公共功能
"""

import logging
import mimetypes
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from fastapi import Request, Response

from utils import HttpUtil, constants

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """处理器基类"""

    @abstractmethod
    async def handle_request(self, request: Request, path: str) -> Response:
        """
        处理请求的抽象方法，子类必须实现

        Args:
            request: FastAPI 请求对象
            path: 请求路径

        Returns:
            FastAPI 响应对象
        """
        pass

    @staticmethod
    def build_full_url(base_url: str, path: str, query: Optional[str] = None) -> str:
        """
        构建完整的 URL

        Args:
            base_url: 基础 URL
            path: 路径部分
            query: 查询参数字符串（可选）

        Returns:
            完整的 URL
        """
        return HttpUtil.build_full_url(base_url, path, query)

    @staticmethod
    async def read_request_body(request: Request) -> bytes:
        """
        读取请求体

        Args:
            request: FastAPI 请求对象

        Returns:
            请求体字节数据
        """
        return await request.body()

    @staticmethod
    def build_response(
        content: bytes,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        path: Optional[str] = None,
    ) -> Response:
        """
        构建 FastAPI 响应对象

        Args:
            content: 响应内容
            status_code: HTTP 状态码
            headers: 响应头字典
            path: 请求路径（用于推测 MIME 类型）

        Returns:
            FastAPI 响应对象
        """
        headers = headers or {}

        # 如果没有 Content-Type，尝试根据路径猜测
        if "content-type" not in headers and path:
            guessed_type, _ = mimetypes.guess_type(path)
            if guessed_type:
                headers["content-type"] = guessed_type

        # 如果仍然没有 Content-Type，使用默认值
        content_type = headers.get("content-type", constants.DEFAULT_MIME_TYPE)

        return Response(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=content_type,
        )

    @staticmethod
    def log_request(method: str, url: str, mode: str = "") -> None:
        """
        记录请求日志

        Args:
            method: HTTP 方法
            url: 请求 URL
            mode: 模式描述（可选）
        """
        prefix = f"{mode}: " if mode else ""
        logger.info(f"{prefix}{method} request for: {url}")

    @staticmethod
    def log_response(url: str, status_code: int, content_length: int) -> None:
        """
        记录响应日志

        Args:
            url: 请求 URL
            status_code: 响应状态码
            content_length: 响应内容长度
        """
        logger.debug(f"Response for {url}: status={status_code}, length={content_length}")
