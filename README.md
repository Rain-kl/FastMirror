# FastMirror

一个基于 FastAPI 的智能反代框架，支持反代、本地和半代理三种运行模式。

## 功能特性

### 1. 三种运行模式

- **反代模式 (Proxy Mode)**: 将请求转发到目标服务器，并自动缓存所有响应
- **本地模式 (Local Mode)**: 完全从本地缓存读取，不发起任何网络请求
- **半代理模式 (Hybrid Mode)**: 智能缓存策略，优先使用本地缓存，不存在时自动代理并缓存

### 2. 智能缓存

- **GET 请求**: 缓存到 `./cache/{domain}/get/` 目录，按 URL 结构组织
- **POST 请求**: 缓存到 `./cache/{domain}/post/` 目录，使用请求体的 MD5 哈希值作为文件名
- **多编码支持**: 自动检测网站编码（GBK、UTF-8 等），统一转换为 UTF-8 存储
- **元数据保存**: 自动保存响应头、状态码和请求参数

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
- `--cache-dir`: 缓存目录 (默认: ./cache)
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
- `--target`: 原始目标服务器 URL (可选，用于构建缓存查找路径)
- 其他参数同反代模式

### 半代理模式

半代理模式结合了反代和本地模式的优势，智能地使用缓存：

```bash
# 基本用法
python main.py --mode hybrid --target http://example.com

# 自定义配置
python main.py --mode hybrid --target http://example.com --port 8080

# 启用调试日志
python main.py --mode hybrid --target http://example.com --log-level DEBUG
```

**参数说明:**
- `--mode hybrid`: 指定半代理模式
- `--target`: 目标服务器 URL (必需)
- 其他参数同反代模式

**工作原理:**
1. 收到请求时，首先检查本地缓存是否存在
2. 如果缓存存在，直接返回缓存内容（快速）
3. 如果缓存不存在，转发到目标服务器并缓存响应
4. 适合开发和测试场景，既能利用缓存加速，又能获取最新数据

## 使用场景

### 场景 1: 完整缓存收集（反代模式）

适用于首次抓取网站内容：

```bash
# 1. 启动反代模式
python main.py --mode proxy --target http://example.com --port 8000

# 2. 通过浏览器访问 http://localhost:8000
# 3. 浏览网站的各个页面，所有内容都会被缓存
```

### 场景 2: 完全离线使用（本地模式）

适用于离线环境或需要极速访问：

```bash
# 1. 启动本地模式
python main.py --mode local --target http://example.com --port 8000

# 2. 访问 http://localhost:8000
# 3. 所有请求直接从缓存读取，无需网络连接
```

### 场景 3: 智能缓存（半代理模式）

适用于开发和测试，自动利用缓存加速：

```bash
# 1. 启动半代理模式
python main.py --mode hybrid --target http://example.com --port 8000

# 2. 访问 http://localhost:8000
# 3. 已缓存的内容即时返回，未缓存的自动代理并缓存
```

## 缓存结构

所有缓存统一存放在 `./cache/` 目录下，按域名和请求类型分类：

### GET 请求缓存

```
./cache/
├── example.com/
│   └── get/
│       ├── index.html          # 首页
│       ├── index.html.meta     # 首页元数据（headers + status_code）
│       ├── about/
│       │   └── index.html      # /about/ 页面
│       ├── style.css           # CSS 文件
│       └── images/
│           └── logo.png        # 图片文件
```

### POST 请求缓存

POST 请求使用请求体的 MD5 哈希值作为文件名，支持同一 URL 不同参数的缓存：

```
./cache/
├── example.com/
│   └── post/
│       └── api/
│           └── login/
│               ├── 5d41402abc4b2a76b9719d911017c592  # {"user":"alice"} 的缓存
│               └── 9f9d51bc70ef21ca5c14f307980a29d8  # {"user":"bob"} 的缓存
```

**特点:**
- POST 缓存文件无扩展名
- 文件内容为 JSON 格式，包含：`status_code`、`headers`、`content`、`request_body`
- 不同请求体产生不同的缓存文件

## 技术架构

### 核心模块

- `config.py`: 配置管理（支持三种运行模式）
- `core/cache_manager.py`: 缓存读写、路径生成、编码检测
- `core/proxy_handler.py`: 反代模式请求处理
- `core/local_handler.py`: 本地模式请求处理
- `core/hybrid_handler.py`: 半代理模式请求处理
- `custom/custom_routes.py`: 自定义路由（本地模式优先）
- `main.py`: 主入口和路由管理

### 技术栈

- **FastAPI**: 高性能 Web 框架
- **httpx**: 异步 HTTP 客户端（用于反代）
- **chardet**: 编码自动检测（支持多种编码）
- **Pydantic**: 配置管理和数据验证

## 注意事项

1. **POST 请求缓存**: 
   - 使用请求体的 MD5 哈希值作为缓存文件名
   - 半代理和本地模式需要请求体完全匹配才能命中缓存
   - 不同请求体会生成不同的缓存文件

2. **编码支持**: 
   - 自动检测网站编码（UTF-8、GBK、GB2312 等）
   - 所有缓存内容统一转换为 UTF-8 存储
   - 支持中文网站和多语言内容

3. **运行模式选择**: 
   - **反代模式**: 适合首次完整抓取，所有内容以远端为准
   - **本地模式**: 适合离线使用，所有内容以本地为准
   - **半代理模式**: 适合开发测试，自动利用缓存加速

4. **性能优化**: 
   - 首次访问（反代/半代理）需要访问远程服务器
   - 后续访问（本地/半代理缓存命中）速度极快
   - 半代理模式可显著减少网络请求数量

## 高级功能

- [x] 三种运行模式（反代/本地/半代理）
- [x] 智能 POST 缓存（基于请求体 MD5）
- [x] 多编码自动检测与转换
- [x] 定制化接口支持
- [ ] 缓存过期管理
- [ ] 缓存统计和管理界面
- [ ] 支持 HTTPS 代理

## 许可证

MIT License
