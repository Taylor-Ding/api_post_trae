#!/bin/bash

# 数据一致性自动化核对工具启动脚本

echo "=== 数据一致性自动化核对工具 ==="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python 3 未安装"
    exit 1
fi

# 安装依赖
echo "正在安装依赖..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo "依赖安装成功"

# 执行主脚本
echo "正在执行数据一致性检查..."
python3 main.py

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "执行完成"
else
    echo "执行失败"
    exit 1
fi