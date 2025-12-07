"""
常量定义
"""

from typing import Final

# HTTP 方法
HTTP_METHOD_GET: Final[str] = "GET"
HTTP_METHOD_POST: Final[str] = "POST"
HTTP_METHOD_PUT: Final[str] = "PUT"
HTTP_METHOD_DELETE: Final[str] = "DELETE"
HTTP_METHOD_PATCH: Final[str] = "PATCH"
HTTP_METHOD_HEAD: Final[str] = "HEAD"
HTTP_METHOD_OPTIONS: Final[str] = "OPTIONS"

# 支持缓存的 HTTP 方法
CACHEABLE_METHODS: Final[tuple[str, ...]] = (HTTP_METHOD_GET, HTTP_METHOD_POST)

# 缓存相关常量
CACHE_DIR_GET: Final[str] = "get"
CACHE_DIR_POST: Final[str] = "post"
CACHE_DIR_PARAMS: Final[str] = "params"
CACHE_DIR_ROOT: Final[str] = "root"
CACHE_FILE_INDEX: Final[str] = "index.html"
CACHE_FILE_EXTENSION_META: Final[str] = ".meta"
CACHE_FILE_EXTENSION_JSON: Final[str] = ".json"

# 默认 MIME 类型
DEFAULT_MIME_TYPE: Final[str] = "application/octet-stream"
MIME_TYPE_HTML: Final[str] = "text/html"
MIME_TYPE_JSON: Final[str] = "application/json"

# HTTP 状态码
HTTP_STATUS_OK: Final[int] = 200
HTTP_STATUS_NOT_FOUND: Final[int] = 404
HTTP_STATUS_INTERNAL_ERROR: Final[int] = 500
HTTP_STATUS_GATEWAY_TIMEOUT: Final[int] = 504

# 日志相关
LOG_PREVIEW_LENGTH: Final[int] = 100

# 编码
ENCODING_UTF8: Final[str] = "utf-8"
