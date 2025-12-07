# FastMirror - AI Coding Agent Instructions

## Project Overview

FastMirror 是一个 基于 FastAPI 的反向代理框架，具有双运行模式和智能缓存能力。它像一个“中间人”，既可以代理请求并缓存响应，也可以在离线环境下完全从本地缓存提供服务。

### Core Architecture: Two-Mode System

核心架构：两种模式

代理模式 (--mode proxy)：
• 通过 ProxyHandler 将请求转发到目标服务器
• 自动缓存所有 GET/POST 响应
• 必须指定 --target
• 入口：main.py → ProxyHandler.handle_request()

本地模式 (--mode local)：
• 使用 LocalHandler 完全从文件系统缓存提供响应
• 不会向远程服务器发起任何网络请求
• --target 可选（仅用于生成缓存路径）
• 入口：main.py → LocalHandler.handle_request()

### Component Responsibilities

```
main.py              # FastAPI 应用、CLI 参数解析、模式路由
config.py            # Pydantic 配置，加载 .env
core/
  cache_manager.py   # 缓存读写与路径生成逻辑
  proxy_handler.py   # 远程转发与响应缓存
  local_handler.py   # 从缓存读取与 MIME 类型处理
custom/
  custom_routes.py   # 自定义路由（本地模式下优先级最高）
```

## Critical Cache Path Logic

**Cache paths mirror URL structure** - understanding this is essential:

```python
# GET 请求: ./cache/{domain}/get/{path}
http://example.com/about → ./cache/example.com/get/about/index.html
http://example.com/api.css → ./cache/example.com/get/api.css

# POST 请求: ./cache/{domain}/post/{path}/{md5(body)}
# 使用请求体的 MD5 哈希值作为文件名，支持相同 URL 不同 body 的缓存
POST http://example.com/api/data {"user":"alice"} → ./cache/example.com/post/api/data/5d41402abc4b2a76b9719d911017c592
POST http://example.com/api/data {"user":"bob"}   → ./cache/example.com/post/api/data/9f9d51bc70ef21ca5c14f307980a29d8

# 元数据：{file}.meta （仅 GET）
./cache/example.com/get/about/index.html.meta  # stores headers + status_code
```

**注意**：只缓存 GET 和 POST 请求，其他 HTTP 方法不记录。POST 缓存文件无扩展名，内容为 JSON 格式。

See `CacheManager._get_cache_path()` for exact logic - it handles trailing slashes, missing extensions, domain extraction, and MD5 hashing for POST bodies.

## Development Workflows

### Running the Application

```bash
# 代理模式（用于采集缓存）
uv run main.py --mode proxy --target http://example.com --port 8000

# 本地模式（离线服务）
uv run main.py --mode local --target http://example.com --port 8000

# 使用脚本快速启动
bash start.sh
```

**Configuration precedence**: CLI args > .env file > defaults (see `Config` in `config.py`)

### Adding Custom Routes

In local mode, **custom routes in `custom/custom_routes.py` take precedence** over cached responses. This is FastMirror's override mechanism:

```python
# custom/custom_routes.py
@custom_router.get("/api/custom")
async def custom_api():
    return {"custom": True}  # Overrides cache for this path
```

Routes are registered via `app.include_router(custom_router)` in `main.py` before the catch-all route.

### Key Technical Decisions

1. **Headers cleaned twice**:

   - In `ProxyHandler`: Remove `content-encoding` because httpx auto-decompresses
   - In `CacheManager.save_response()`: Also strip `content-length`, `transfer-encoding`
   - Why: Prevents double-decompression errors and chunking issues

2. **POST cache format**:

   - JSON with `{status_code, headers, content, request_body}` structure
   - Files stored without extension at `{path}/{md5(body)}`
   - Different request bodies to same URL create separate cache files
   - Local mode requires matching body to retrieve correct cached response
   - See `CacheManager.save_response()` POST branch and MD5 hashing logic

3. **Encoding detection and conversion**:

   - Uses `chardet` to detect content encoding (supports non-UTF-8 sites)
   - All cached content automatically converted to UTF-8
   - `_detect_and_decode()` method handles: UTF-8 → chardet detection → fallback with errors='replace'
   - Applies to both response content and request body in POST requests

4. **Redirect handling**:
   - `ProxyHandler` rewrites `Location` headers pointing to target domain
   - Preserves external redirects and relative paths
   - See lines 81-97 in `proxy_handler.py`

## Common Patterns

**Reading config**: Always use `app_config` singleton from `config.py`, never re-instantiate `Config()`

**Logging**: Use module-level logger (`logger = logging.getLogger(__name__)`), level set via `--log-level`

**Path handling**: Use `pathlib.Path`, all cache paths auto-created via `mkdir(parents=True, exist_ok=True)`

**Async clients**: `ProxyHandler.client` is `httpx.AsyncClient`, closed in `lifespan` cleanup

## Testing & Debugging

```bash
# Enable verbose logging
uv run main.py --mode proxy --target http://example.com --log-level DEBUG

# Check cache structure
ls -R ./cache/
cat ./cache/example.com/index.html.meta

# Test custom routes (local mode)
curl http://localhost:8000/api/custom
```

**No test suite exists** - manual testing via curl/browser is current practice.

## Dependencies & Tooling

- **Package manager**: `uv` (preferred) or `pip`
- **Key deps**: `fastapi[standard]`, `httpx`, `beautifulsoup4`, `pydantic-settings`
- **Python version**: >=3.12 (see `pyproject.toml`)
- **Mirror**: Tsinghua PyPI mirror configured in `pyproject.toml`

Install: `uv sync` or `pip install -e .`

## When Modifying Code

- **Adding routes**: Put in `custom/custom_routes.py`, use `@custom_router` decorator
- **Changing cache logic**: Modify `CacheManager` methods, ensure GET/POST branches stay consistent
- **New config options**: Add to `Config` class in `config.py`, document in README
- **Header handling**: Check both `ProxyHandler` and `CacheManager` cleaning logic
