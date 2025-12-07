# 使用官方 Python 3.12 slim 镜像作为基础
FROM ghcr.io/astral-sh/uv:alpine

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --frozen --no-dev

# 创建缓存目录
RUN mkdir -p /app/cache

# 暴露端口
EXPOSE 8000

# 启动命令 (可通过环境变量覆盖)
CMD ["uv", "run", "main.py"]