"""
缓存管理模块
负责处理请求缓存的读写操作
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, unquote


class CacheManager:
    """缓存管理器"""

    def __init__(
        self, cache_dir: str = "./cache", cache_post_dir: str = "./cache_post"
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_post_dir = Path(cache_post_dir)

        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_post_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str, method: str = "GET") -> Path:
        """
        根据 URL 和请求方法生成缓存文件路径

        Args:
            url: 请求的完整 URL
            method: HTTP 方法 (GET 或 POST)

        Returns:
            缓存文件的路径
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        path = unquote(parsed.path).strip("/")

        if method.upper() == "GET":
            # GET 请求: ./cache/example.com/path/to/resource/index.html
            base_dir = self.cache_dir / domain

            if not path:
                # 根路径
                cache_path = base_dir / "index.html"
            elif path.endswith("/"):
                # 目录路径
                cache_path = base_dir / path / "index.html"
            else:
                # 文件路径
                # 检查是否有扩展名
                if "." in Path(path).name:
                    cache_path = base_dir / path
                else:
                    # 没有扩展名,作为目录处理
                    cache_path = base_dir / path / "index.html"

            return cache_path

        elif method.upper() == "POST":
            # POST 请求: ./cache_post/example.com/path/to/endpoint.json
            base_dir = self.cache_post_dir / domain

            if not path:
                cache_path = base_dir / "index.json"
            else:
                # 确保以 .json 结尾
                if not path.endswith(".json"):
                    cache_path = base_dir / f"{path}.json"
                else:
                    cache_path = base_dir / path

            return cache_path

        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def save_response(
        self,
        url: str,
        method: str,
        content: bytes,
        headers: Optional[Dict[str, str]] = None,
        status_code: int = 200,
    ) -> None:
        """
        保存响应到缓存

        Args:
            url: 请求的完整 URL
            method: HTTP 方法
            content: 响应内容
            headers: 响应头
            status_code: HTTP 状态码
        """
        cache_path = self._get_cache_path(url, method)

        # 确保父目录存在
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # 清理headers,移除可能导致问题的header
        # httpx已自动解压,移除content-encoding避免浏览器二次解压
        cleaned_headers = dict(headers or {})
        headers_to_remove = ["content-encoding", "content-length", "transfer-encoding"]
        for header in headers_to_remove:
            cleaned_headers.pop(header, None)

        if method.upper() == "GET":
            # GET 请求直接保存内容
            cache_path.write_bytes(content)

            # 保存元数据 (headers 和 status_code)
            meta_path = cache_path.with_suffix(cache_path.suffix + ".meta")
            meta_data = {"status_code": status_code, "headers": cleaned_headers}
            meta_path.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False))

        elif method.upper() == "POST":
            # POST 请求保存为 JSON
            data = {
                "status_code": status_code,
                "headers": cleaned_headers,
                "content": content.decode("utf-8", errors="ignore"),
            }
            cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def get_response(self, url: str, method: str = "GET") -> Optional[Dict[str, Any]]:
        """
        从缓存读取响应

        Args:
            url: 请求的完整 URL
            method: HTTP 方法

        Returns:
            包含响应数据的字典,如果缓存不存在则返回 None
            字典格式: {
                "content": bytes,
                "headers": dict,
                "status_code": int
            }
        """
        cache_path = self._get_cache_path(url, method)

        if not cache_path.exists():
            return None

        if method.upper() == "GET":
            # 读取内容
            content = cache_path.read_bytes()

            # 读取元数据
            meta_path = cache_path.with_suffix(cache_path.suffix + ".meta")
            if meta_path.exists():
                meta_data = json.loads(meta_path.read_text())
                headers = meta_data.get("headers", {})
                status_code = meta_data.get("status_code", 200)
            else:
                headers = {}
                status_code = 200

            return {"content": content, "headers": headers, "status_code": status_code}

        elif method.upper() == "POST":
            # POST 请求从 JSON 读取
            data = json.loads(cache_path.read_text())
            return {
                "content": data.get("content", "").encode("utf-8"),
                "headers": data.get("headers", {}),
                "status_code": data.get("status_code", 200),
            }

        return None

    def has_cache(self, url: str, method: str = "GET") -> bool:
        """
        检查缓存是否存在

        Args:
            url: 请求的完整 URL
            method: HTTP 方法

        Returns:
            缓存是否存在
        """
        cache_path = self._get_cache_path(url, method)
        return cache_path.exists()
