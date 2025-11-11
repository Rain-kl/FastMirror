"""
FastMirror - 反代框架主入口
"""

import argparse
import logging
import sys
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from config import app_config, RunMode, Config
from cache_manager import CacheManager
from proxy_handler import ProxyHandler
from local_handler import LocalHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 全局变量
cache_manager: CacheManager = None
proxy_handler: ProxyHandler = None
local_handler: LocalHandler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global cache_manager, proxy_handler, local_handler

    # 初始化缓存管理器
    cache_manager = CacheManager(
        cache_dir=app_config.cache_dir, cache_post_dir=app_config.cache_post_dir
    )

    # 根据模式初始化对应的处理器
    if app_config.mode == RunMode.PROXY:
        if not app_config.target_url:
            logger.error("反代模式需要指定 target_url")
            sys.exit(1)

        proxy_handler = ProxyHandler(
            target_url=app_config.target_url, cache_manager=cache_manager
        )
        logger.info(
            f"启动反代模式: {app_config.target_url} -> http://{app_config.host}:{app_config.port}"
        )

    elif app_config.mode == RunMode.LOCAL:
        local_handler = LocalHandler(
            cache_manager=cache_manager,
            target_url=app_config.target_url or "http://localhost",
        )
        logger.info(f"启动本地模式: http://{app_config.host}:{app_config.port}")

    yield

    # 清理资源
    if proxy_handler:
        await proxy_handler.close()


# 创建 FastAPI 应用
app = FastAPI(
    title="FastMirror",
    description="反代框架 - 支持反代模式和本地模式",
    version="1.0.0",
    lifespan=lifespan,
)


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def catch_all(request: Request, path: str = ""):
    """
    捕获所有请求的路由(包括根路径)
    根据运行模式调用对应的处理器
    """
    if app_config.mode == RunMode.PROXY:
        return await proxy_handler.handle_request(request, path)
    elif app_config.mode == RunMode.LOCAL:
        return await local_handler.handle_request(request, path)


def main():
    """主函数"""
    import uvicorn

    # 注意: 配置已通过 .env 文件加载 (见 config.py)
    # 命令行参数将覆盖 .env 中的配置

    parser = argparse.ArgumentParser(
        description="FastMirror - 反代框架 (支持 .env 配置文件)",
        epilog="提示: 可以创建 .env 文件来配置默认参数,命令行参数将覆盖 .env 中的配置",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["proxy", "local"],
        help="运行模式: proxy(反代模式) 或 local(本地模式) [默认: 从 .env 读取或 proxy]",
    )
    parser.add_argument(
        "--target", type=str, help="目标服务器 URL (反代模式必需) [默认: 从 .env 读取]"
    )
    parser.add_argument(
        "--host", type=str, help="监听地址 [默认: 从 .env 读取或 0.0.0.0]"
    )
    parser.add_argument("--port", type=int, help="监听端口 [默认: 从 .env 读取或 8000]")
    parser.add_argument(
        "--cache-dir",
        type=str,
        help="GET 请求缓存目录 [默认: 从 .env 读取或 ./cache]",
    )
    parser.add_argument(
        "--cache-post-dir",
        type=str,
        help="POST 请求缓存目录 [默认: 从 .env 读取或 ./cache_post]",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 [默认: 从 .env 读取或 INFO]",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="环境配置文件路径 [默认: .env]",
    )

    args = parser.parse_args()

    # 如果指定了自定义 .env 文件,重新加载配置
    if args.env_file != ".env":
        from pathlib import Path

        if Path(args.env_file).exists():
            global app_config
            app_config = Config(_env_file=args.env_file)
            logger.info(f"从 {args.env_file} 加载配置")

    # 命令行参数覆盖配置文件
    if args.mode:
        app_config.mode = RunMode(args.mode)
    if args.target:
        app_config.target_url = args.target
    if args.host:
        app_config.host = args.host
    if args.port:
        app_config.port = args.port
    if args.cache_dir:
        app_config.cache_dir = args.cache_dir
    if args.cache_post_dir:
        app_config.cache_post_dir = args.cache_post_dir
    if args.log_level:
        app_config.log_level = args.log_level

    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, app_config.log_level))

    # 打印当前配置
    logger.info("=" * 60)
    logger.info("FastMirror 启动配置:")
    logger.info(f"  运行模式: {app_config.mode.value}")
    logger.info(f"  监听地址: {app_config.host}:{app_config.port}")
    if app_config.target_url:
        logger.info(f"  目标服务器: {app_config.target_url}")
    logger.info(f"  GET 缓存目录: {app_config.cache_dir}")
    logger.info(f"  POST 缓存目录: {app_config.cache_post_dir}")
    logger.info(f"  日志级别: {app_config.log_level}")
    logger.info("=" * 60)

    # 验证反代模式必须提供 target_url
    if app_config.mode == RunMode.PROXY and not app_config.target_url:
        logger.error("反代模式必须指定目标服务器!")
        logger.error("请通过以下方式之一指定:")
        logger.error("  1. 在 .env 文件中设置 TARGET_URL")
        logger.error("  2. 使用命令行参数: --target http://example.com")
        sys.exit(1)

    # 启动服务器
    uvicorn.run(
        app,
        host=app_config.host,
        port=app_config.port,
        log_level=app_config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
