#!/bin/bash

echo "=========================================="
echo "FortiGate Debug Monitor - 启动脚本"
echo "=========================================="
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

echo "✓ Python3 已安装: $(python3 --version)"
echo ""

# 检查是否已安装依赖
echo "检查依赖..."
if python3 -c "import flask" 2>/dev/null; then
    echo "✓ Flask 已安装"
else
    echo "⚠ Flask 未安装,正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "=========================================="
echo "启动后端服务器..."
echo "=========================================="
echo ""
echo "后端API将运行在: http://localhost:5000"
echo "前端页面请打开: index.html"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动Flask应用
python3 app.py
