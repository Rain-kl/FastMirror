#!/bin/bash
# FastMirror 快速启动脚本

echo "FastMirror 启动脚本"
echo "===================="
echo ""
echo "请选择运行模式:"
echo "1) 反代模式 (Proxy Mode)"
echo "2) 本地模式 (Local Mode)"
echo ""
read -p "请输入选项 (1 或 2): " choice

case $choice in
    1)
        echo ""
        read -p "请输入目标服务器 URL (例如: http://example.com): " target_url
        read -p "请输入监听端口 (默认: 8000): " port
        port=${port:-8000}
        
        echo ""
        echo "启动反代模式..."
        echo "目标: $target_url"
        echo "端口: $port"
        echo ""
        
        uv run main.py --mode proxy --target "$target_url" --port "$port"
        ;;
    2)
        read -p "请输入原始目标服务器 URL (可选,用于查找缓存): " target_url
        read -p "请输入监听端口 (默认: 8000): " port
        port=${port:-8000}
        
        echo ""
        echo "启动本地模式..."
        if [ -n "$target_url" ]; then
            echo "目标: $target_url"
        fi
        echo "端口: $port"
        echo ""
        
        if [ -n "$target_url" ]; then
            uv run main.py --mode local --target "$target_url" --port "$port"
        else
            uv run main.py --mode local --port "$port"
        fi
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
