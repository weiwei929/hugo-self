#!/bin/bash
echo 'Hugo-Self WSL2 启动器'
echo '==================='

# 清除代理设置
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY='localhost,127.0.0.1,0.0.0.0'

echo '代理设置已清除'

# 检查环境
python3 --version
hugo version

# 清理端口
pkill -f hugo 2>/dev/null || true
pkill -f python.*start_separated 2>/dev/null || true
sleep 2

echo '启动服务...'
python3 scripts/start_separated.py
