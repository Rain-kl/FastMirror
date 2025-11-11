"""
定制化接口示例

在本地模式下,你可以创建定制化接口来覆盖缓存的响应。
将此文件的逻辑集成到 main.py 中,以支持自定义路由。

使用方法:
1. 在 main.py 中导入此模块
2. 在本地模式下,优先匹配定制化接口
3. 如果没有匹配到定制化接口,则使用缓存响应
"""

from fastapi import APIRouter, Request
from typing import Dict, Any

# 创建路由器
custom_router = APIRouter()


@custom_router.get("/api/custom")
async def custom_api():
    """
    自定义接口示例
    在本地模式下,访问 /api/custom 会优先使用此接口
    """
    return {
        "message": "这是一个定制化接口",
        "data": {"custom": True, "source": "local_override"},
    }


@custom_router.post("/api/custom-post")
async def custom_post_api(request: Request):
    """
    自定义 POST 接口示例
    """
    body = await request.json()
    return {"message": "收到自定义 POST 请求", "received": body, "processed": True}


# 可以添加更多自定义路由...
