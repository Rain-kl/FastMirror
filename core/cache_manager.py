"""
缓存管理模块
负责处理请求缓存的读写操作
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from utils import EncodingUtil, CachePathUtil, HttpUtil, constants


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)

        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(
            self, url: str, method: str = "GET", body: Optional[bytes] = None
    ) -> Path:
        """
        根据 URL 和请求方法生成缓存文件路径

        Args:
            url: 请求的完整 URL
            method: HTTP 方法 (GET 或 POST)
            body: 请求体 (POST 请求需要)

        Returns:
            缓存文件的路径
        """
        domain, path, query = CachePathUtil.extract_url_parts(url)

        if method.upper() == constants.HTTP_METHOD_GET:
            return CachePathUtil.build_get_cache_path(
                self.cache_dir, domain, path, query
            )
        elif method.upper() == constants.HTTP_METHOD_POST:
            return CachePathUtil.build_post_cache_path(
                self.cache_dir, domain, path, body
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def save_response(
            self,
            url: str,
            method: str,
            content: bytes,
            headers: Optional[Dict[str, str]] = None,
            status_code: int = 200,
            body: Optional[bytes] = None,
    ) -> None:
        """
        保存响应到缓存

        Args:
            url: 请求的完整 URL
            method: HTTP 方法
            content: 响应内容
            headers: 响应头
            status_code: HTTP 状态码
            body: 请求体 (POST 请求需要)
        """
        cache_path = self._get_cache_path(url, method, body)

        # 确保父目录存在
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # 清理 headers，使用工具类
        cleaned_headers = HttpUtil.clean_response_headers(headers or {})

        if method.upper() == constants.HTTP_METHOD_GET:
            _, _, query = CachePathUtil.extract_url_parts(url)
            
            # 如果有查询参数，使用 JSON 格式保存（类似 POST）
            if query:
                data = {
                    "status_code": status_code,
                    "headers": cleaned_headers,
                    "content": EncodingUtil.detect_and_decode(content),
                    "query_params": query,
                }
                cache_path.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding=constants.ENCODING_UTF8,
                )
            else:
                # GET 请求无参数直接保存内容
                cache_path.write_bytes(content)

                # 保存元数据 (headers 和 status_code)
                meta_path = cache_path.with_suffix(
                    cache_path.suffix + constants.CACHE_FILE_EXTENSION_META
                )
                meta_data = {"status_code": status_code, "headers": cleaned_headers}
                meta_path.write_text(
                    json.dumps(meta_data, indent=2, ensure_ascii=False),
                    encoding=constants.ENCODING_UTF8,
                )

        elif method.upper() == constants.HTTP_METHOD_POST:
            # POST 请求保存为 JSON (无扩展名)
            data = {
                "status_code": status_code,
                "headers": cleaned_headers,
                "content": EncodingUtil.detect_and_decode(content),
                "request_body": EncodingUtil.detect_and_decode(body) if body else "",
            }
            cache_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding=constants.ENCODING_UTF8,
            )

    def get_response(
            self, url: str, method: str = "GET", body: Optional[bytes] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从缓存读取响应

        Args:
            url: 请求的完整 URL
            method: HTTP 方法
            body: 请求体 (POST 请求需要)

        Returns:
            包含响应数据的字典,如果缓存不存在则返回 None
            字典格式: {
                "content": bytes,
                "headers": dict,
                "status_code": int
            }
        """
        cache_path = self._get_cache_path(url, method, body)

        if not cache_path.exists():
            return None

        if method.upper() == constants.HTTP_METHOD_GET:
            _, _, query = CachePathUtil.extract_url_parts(url)
            
            # 如果有查询参数，从 JSON 格式读取
            if query:
                data = json.loads(
                    cache_path.read_text(encoding=constants.ENCODING_UTF8)
                )
                return {
                    "content": data.get("content", "").encode(constants.ENCODING_UTF8),
                    "headers": data.get("headers", {}),
                    "status_code": data.get("status_code", constants.HTTP_STATUS_OK),
                }
            else:
                # GET 请求无参数直接读取内容
                content = cache_path.read_bytes()

                # 读取元数据
                meta_path = cache_path.with_suffix(
                    cache_path.suffix + constants.CACHE_FILE_EXTENSION_META
                )
                if meta_path.exists():
                    meta_data = json.loads(
                        meta_path.read_text(encoding=constants.ENCODING_UTF8)
                    )
                    headers = meta_data.get("headers", {})
                    status_code = meta_data.get("status_code", constants.HTTP_STATUS_OK)
                else:
                    headers = {}
                    status_code = constants.HTTP_STATUS_OK

                return {"content": content, "headers": headers, "status_code": status_code}

        elif method.upper() == constants.HTTP_METHOD_POST:
            # POST 请求从 JSON 读取
            data = json.loads(cache_path.read_text(encoding=constants.ENCODING_UTF8))
            return {
                "content": data.get("content", "").encode(constants.ENCODING_UTF8),
                "headers": data.get("headers", {}),
                "status_code": data.get("status_code", constants.HTTP_STATUS_OK),
            }

        return None

    def has_cache(
            self, url: str, method: str = "GET", body: Optional[bytes] = None
    ) -> bool:
        """
        检查缓存是否存在

        Args:
            url: 请求的完整 URL
            method: HTTP 方法
            body: 请求体 (POST 请求需要)

        Returns:
            缓存是否存在
        """
        cache_path = self._get_cache_path(url, method, body)
        return cache_path.exists()
