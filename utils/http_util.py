"""
HTTP 相关工具函数
"""

from typing import Dict, Optional
from urllib.parse import urlparse


class HttpUtil:
    """HTTP 工具类"""

    # 需要清理的响应头列表
    HEADERS_TO_REMOVE = [
        "content-encoding",  # httpx 已自动解压，需移除避免浏览器二次解压
        "content-length",  # 内容长度会自动计算
        "transfer-encoding",  # 避免分块传输问题
        "host",  # 代理时需要移除
        "connection",  # 代理时需要移除
    ]

    @staticmethod
    def clean_headers(
        headers: Dict[str, str], remove_list: Optional[list[str]] = None
    ) -> Dict[str, str]:
        """
        清理 HTTP 头，移除可能导致问题的 headers

        Args:
            headers: 原始 headers 字典
            remove_list: 要移除的 header 名称列表，默认使用 HEADERS_TO_REMOVE

        Returns:
            清理后的 headers 字典
        """
        if remove_list is None:
            remove_list = HttpUtil.HEADERS_TO_REMOVE

        cleaned = dict(headers)
        for header in remove_list:
            cleaned.pop(header, None)

        return cleaned

    @staticmethod
    def clean_proxy_request_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """
        清理代理请求头，移除不应该转发的 headers

        Args:
            headers: 原始请求 headers

        Returns:
            清理后的 headers
        """
        return HttpUtil.clean_headers(headers, ["host", "connection"])

    @staticmethod
    def clean_response_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """
        清理响应头，移除可能导致问题的 headers

        Args:
            headers: 原始响应 headers

        Returns:
            清理后的 headers
        """
        return HttpUtil.clean_headers(
            headers, ["content-encoding", "content-length", "transfer-encoding"]
        )

    @staticmethod
    def build_full_url(base_url: str, path: str, query: Optional[str] = None) -> str:
        """
        构建完整的 URL

        Args:
            base_url: 基础 URL（如 http://example.com）
            path: 路径部分
            query: 查询参数字符串（可选）

        Returns:
            完整的 URL
        """
        base_url = base_url.rstrip("/")
        path = path.lstrip("/")
        full_url = f"{base_url}/{path}" if path else base_url

        if query:
            full_url += f"?{query}"

        return full_url

    @staticmethod
    def rewrite_location_header(
        location: str, target_url: str
    ) -> tuple[str, bool]:
        """
        重写 Location 响应头，将目标服务器地址替换为代理地址

        Args:
            location: 原始 Location 值
            target_url: 目标服务器 URL

        Returns:
            (重写后的 location, 是否被修改)
        """
        target_url = target_url.rstrip("/")

        # 如果 Location 指向目标服务器，去掉目标服务器部分
        if location.startswith(target_url):
            new_location = location[len(target_url) :]
            return new_location or "/", True

        # 如果是其他完整 URL 或相对路径，保持不变
        return location, False

    @staticmethod
    def extract_domain(url: str) -> str:
        """
        从 URL 中提取域名

        Args:
            url: 完整的 URL

        Returns:
            域名部分
        """
        parsed = urlparse(url)
        return parsed.netloc
