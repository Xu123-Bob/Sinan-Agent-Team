#!/usr/bin/env bash
set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║          司南 (Sinan) 安装助手                        ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo

# 1. 检查 Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ 未找到 python3，请先安装 Python 3.10~3.12"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

echo "检测到 Python $PY_VERSION"

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "❌ Python 版本过低，需要 3.10+"
    exit 1
fi
if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 14 ]; then
    echo "⚠️  Python $PY_VERSION 兼容性可能有问题，推荐 3.10~3.12"
    read -p "继续安装？(y/n) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# 2. 询问是否创建 venv
read -p "是否创建虚拟环境？(推荐 y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -m venv .venv
    source .venv/bin/activate
    echo "✅ 已激活 venv"
fi

# 3. 安装
echo "正在安装司南..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .

# 4. 验证
echo
echo "验证安装..."
python3 -m agent.doctor

echo
echo "✅ 安装完成！启动方式："
echo "   sinan"
echo "   或"
echo "   python -m agent"