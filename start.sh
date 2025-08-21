#!/bin/bash
set -e  # 出错时遇到错误退出

# 指定 conda 路径
CONDA_PATH="/opt/conda"

# 加载 conda 初始化脚本
source "$CONDA_PATH/etc/profile.d/conda.sh"

# 创建环境（如果不存在才创建）
if ! conda env list | grep -qE "^web\s"; then
    echo ">>> Creating conda environment: web"
    conda create -n web python=3.10 -y
else
    echo ">>> Environment 'web' already exists, skipping creation."
fi

# 激活环境
echo ">>> Activating environment: web"
conda activate web

# 安装依赖
echo ">>> Installing dependencies from requirements_web.txt"
pip config set global.index-url http://mirrors.baidubce.com/pypi/simple/
pip config set global.extra-index-url http://mirrors.baidubce.com/pypi/simple/
pip config set install.trusted-host mirrors.baidubce.com
pip install -r requirements_web.txt
pip list

# 运行程序
echo ">>> Running program"
python run.py
