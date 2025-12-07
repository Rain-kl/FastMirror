# FastMirror

一个基于 FastAPI 的反代框架,支持反代模式和本地缓存模式。

## 功能特性

### 1. 双模式运行

- **反代模式 (Proxy Mode)**: 将请求转发到目标服务器,并自动缓存响应
- **本地模式 (Local Mode)**: 直接从本地缓存读取响应,无需访问远程服务器

### 2. 智能缓存

- GET 请求: 缓存到 `./cache/` 目录,按 URL 结构组织
- POST 请求: 缓存到 `./cache_post/` 目录,以 JSON 格式存储
- 自动保存响应头和状态码

### 3. 灵活配置

- 支持命令行参数配置
- 可自定义缓存目录、监听端口等

## 安装

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

## 使用方法

### 反代模式

在反代模式下,程序会将请求转发到目标服务器,并缓存所有响应:

```bash
# 基本用法
python main.py --mode proxy --target http://example.com

# 自定义端口和缓存目录
python main.py --mode proxy --target http://example.com --port 8080 --cache-dir ./my_cache

# 启用调试日志
python main.py --mode proxy --target http://example.com --log-level DEBUG
```

**参数说明:**
- `--mode proxy`: 指定反代模式
- `--target`: 目标服务器 URL (必需)
- `--host`: 监听地址 (默认: 0.0.0.0)
- `--port`: 监听端口 (默认: 8000)
- `--cache-dir`: GET 请求缓存目录 (默认: ./cache)
- `--cache-post-dir`: POST 请求缓存目录 (默认: ./cache_post)
- `--log-level`: 日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)

### 本地模式

在本地模式下,程序直接从缓存读取响应,不访问远程服务器:

```bash
# 基本用法
python main.py --mode local

# 指定目标 URL (用于构建缓存路径)
python main.py --mode local --target http://example.com

# 自定义配置
python main.py --mode local --port 8080 --cache-dir ./my_cache
```

**参数说明:**

- `--mode local`: 指定本地模式
- `--target`: 原始目标服务器 URL (可选,用于构建缓存查找路径)
- 其他参数同反代模式

## 工作流程

### 典型使用场景

1. **第一阶段: 缓存收集**

   ```bash
   # 启动反代模式
   python main.py --mode proxy --target http://example.com --port 8000
   
   # 通过浏览器访问 http://localhost:8000
   # 所有请求会被转发到 example.com 并缓存到本地
   ```

2. **第二阶段: 离线使用**

   ```bash
   # 启动本地模式
   python main.py --mode local --target http://example.com --port 8000
   
   # 通过浏览器访问 http://localhost:8000
   # 所有请求直接从本地缓存读取,无需网络连接
   ```

## 缓存结构

### GET 请求缓存

```
./cache/
├── example.com/
│   ├── index.html          # 首页
│   ├── index.html.meta     # 首页元数据
│   ├── about/
│   │   └── index.html      # /about/ 页面
│   ├── style.css           # CSS 文件
│   └── images/
│       └── logo.png        # 图片文件
```

### POST 请求缓存

```
./cache_post/
├── example.com/
│   ├── api/
│   │   ├── login.json      # /api/login 接口
│   │   └── data.json       # /api/data 接口
```

## 技术架构

### 核心模块

- `config.py`: 配置管理
- `cache_manager.py`: 缓存读写管理
- `proxy_handler.py`: 反代模式请求处理
- `local_handler.py`: 本地模式请求处理
- `main.py`: 主入口和路由管理

### 技术栈

- **FastAPI**: Web 框架
- **httpx**: HTTP 客户端(用于反代)
- **BeautifulSoup4**: HTML 解析和处理
- **Pydantic**: 配置管理和数据验证

## 注意事项

1. **路径转换**: 反代模式会自动将 HTML 中的绝对路径转换为相对路径,确保在本地模式下资源能正确加载

2. **POST 请求**: 本地模式下,POST 请求的载荷是无效的,只根据 URL 读取缓存

3. **缓存管理**: 
   - 反代模式: 所有内容以远端为准
   - 本地模式: 所有内容以本地为准

4. **性能**: 首次访问(反代模式)需要访问远程服务器,后续访问(本地模式)速度极快

## 高级功能 (TODO)

- [x] 定制化接口支持 (本地模式优先使用自定义接口)
- [ ] 缓存过期管理
- [ ] 缓存统计和管理界面
- [ ] 支持 HTTPS 代理
- [ ] 支持请求重写规则

## 许可证

MIT License
