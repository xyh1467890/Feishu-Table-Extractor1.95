#!/bin/bash
# 飞书多维表格管理工具打包脚本 - macOS/Linux 版本
# 使用 PyInstaller 打包成独立可执行文件

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "飞书多维表格管理工具 - 打包脚本"
echo "========================================="

# 检查是否安装了依赖
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 python3，请先安装 Python 3"
    exit 1
fi

if ! pip3 show pyinstaller &> /dev/null; then
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
fi

echo ""
echo "开始打包..."

# 使用 PyInstaller 打包
pyinstaller --noconfirm --windowed --name "飞书多维表格工具" \
    --icon "$SCRIPT_DIR/icon.png" \
    --add-data "$SCRIPT_DIR/icon.png:." \
    --add-data "$SCRIPT_DIR/README.md:." \
    --add-data "$SCRIPT_DIR/BUILDING_JUDGE_TUTORIAL.md:." \
    "$SCRIPT_DIR/main.py"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "打包成功！"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS 应用位于: $SCRIPT_DIR/dist/飞书多维表格工具.app"
    else
        echo "Linux 可执行文件位于: $SCRIPT_DIR/dist/飞书多维表格工具"
    fi
    echo "========================================="
else
    echo ""
    echo "打包失败，请检查错误信息"
    exit 1
fi
