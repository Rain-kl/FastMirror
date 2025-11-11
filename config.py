"""
配置管理模块
"""

from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class RunMode(str, Enum):
    """运行模式"""

    PROXY = "proxy"  # 反代模式
    LOCAL = "local"  # 本地模式


class Config(BaseSettings):
    """应用配置"""

    # 运行模式
    mode: RunMode = RunMode.PROXY

    # 监听配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 目标服务器配置 (仅反代模式使用)
    target_url: Optional[str] = None

    # 缓存目录配置
    cache_dir: str = "./cache"
    cache_post_dir: str = "./cache_post"

    # 定制化接口目录
    custom_routes_dir: str = "./custom_routes"

    # 超时配置
    request_timeout: int = 30

    # 日志级别
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# 全局配置实例
app_config = Config()
