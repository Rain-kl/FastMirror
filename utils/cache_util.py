"""
缓存路径相关工具函数
"""

import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote

from . import constants


class CachePathUtil:
    """缓存路径工具类"""

    @staticmethod
    def compute_hash(data: bytes) -> str:
        """
        计算数据的 MD5 哈希值

        Args:
            data: 要计算哈希的字节数据

        Returns:
            MD5 哈希值的十六进制字符串
        """
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def extract_url_parts(url: str) -> tuple[str, str, str]:
        """
        从 URL 中提取域名、路径和查询参数

        Args:
            url: 完整的 URL

        Returns:
            (domain, path, query) 元组
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        path = unquote(parsed.path).strip("/")
        query = parsed.query
        return domain, path, query

    @staticmethod
    def build_get_cache_path(
        cache_dir: Path, domain: str, path: str, query: str
    ) -> Path:
        """
        构建 GET 请求的缓存路径

        Args:
            cache_dir: 缓存根目录
            domain: 域名
            path: URL 路径
            query: 查询参数字符串

        Returns:
            缓存文件路径
        """
        base_dir = cache_dir / domain / constants.CACHE_DIR_GET

        # 如果有查询参数，使用 MD5 哈希值作为文件名
        if query:
            query_hash = CachePathUtil.compute_hash(
                query.encode(constants.ENCODING_UTF8)
            )

            if not path:
                # 根路径带参数: ./cache/{domain}/get/params/{md5}
                cache_path = (
                    base_dir
                    / constants.CACHE_DIR_PARAMS
                    / f"{query_hash}{constants.CACHE_FILE_EXTENSION_JSON}"
                )
            else:
                # 带路径和参数: ./cache/{domain}/get/path/to/resource/params/{md5}
                # 需要去掉文件名，只保留目录路径
                path_obj = Path(path)
                if "." in path_obj.name and not path.endswith("/"):
                    # 如果是文件路径（有扩展名），使用其父目录
                    dir_path = path_obj.parent
                else:
                    # 如果是目录路径，直接使用
                    dir_path = path_obj
                
                cache_path = (
                    base_dir
                    / dir_path
                    / constants.CACHE_DIR_PARAMS
                    / f"{query_hash}{constants.CACHE_FILE_EXTENSION_JSON}"
                )
        else:
            # GET 请求无参数: ./cache/{domain}/get/path/to/resource/index.html
            if not path:
                # 根路径
                cache_path = base_dir / constants.CACHE_FILE_INDEX
            elif path.endswith("/"):
                # 目录路径
                cache_path = base_dir / path / constants.CACHE_FILE_INDEX
            else:
                # 文件路径
                # 检查是否有扩展名
                if "." in Path(path).name:
                    cache_path = base_dir / path
                else:
                    # 没有扩展名，作为目录处理
                    cache_path = base_dir / path / constants.CACHE_FILE_INDEX

        return cache_path

    @staticmethod
    def build_post_cache_path(
        cache_dir: Path, domain: str, path: str, body: Optional[bytes]
    ) -> Path:
        """
        构建 POST 请求的缓存路径

        Args:
            cache_dir: 缓存根目录
            domain: 域名
            path: URL 路径
            body: 请求体字节数据

        Returns:
            缓存文件路径
        """
        base_dir = cache_dir / domain / constants.CACHE_DIR_POST

        # 计算请求体的 MD5 哈希值
        body_hash = CachePathUtil.compute_hash(body or b"")

        if not path:
            # 根路径: ./cache/{domain}/post/root/{md5}
            cache_path = (
                base_dir
                / constants.CACHE_DIR_ROOT
                / f"{body_hash}{constants.CACHE_FILE_EXTENSION_JSON}"
            )
        else:
            # 带路径: ./cache/{domain}/post/path/to/endpoint/{md5}
            cache_path = (
                base_dir / path / f"{body_hash}{constants.CACHE_FILE_EXTENSION_JSON}"
            )

        return cache_path
