#!/bin/bash
# Hugo-Self WSL2 优化启动脚本
# 解决代理问题和性能优化

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Hugo-Self WSL2 优化启动器 (分离式架构)${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# 1. 环境优化 - 清除所有代理设置
echo -e "${YELLOW}🧹 清除代理设置...${NC}"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY="localhost,127.0.0.1,0.0.0.0,::1,*.local"

# 检查并清除环境变量
for proxy_var in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY; do
    if [[ -n "${!proxy_var}" ]]; then
        echo -e "${YELLOW}⚠️  检测到代理变量 $proxy_var=${!proxy_var}${NC}"
        unset $proxy_var
    fi
done

echo -e "${GREEN}✅ 代理设置已清除${NC}"

# 2. 性能优化提示
if [[ "$(pwd)" == /mnt/* ]]; then
    echo -e "${PURPLE}⚡ 性能提醒: 当前在Windows文件系统挂载点运行${NC}"
    echo -e "${PURPLE}💡 建议迁移到WSL2原生文件系统以提高性能${NC}"
    echo -e "${BLUE}🔧 迁移命令: cp -r . ~/hugo-self && cd ~/hugo-self${NC}"
    echo -e "${YELLOW}是否继续在当前位置运行? (y/N)${NC}"
    read -t 15 -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}建议先迁移项目再运行${NC}"
        exit 0
    fi
fi

# 3. 检查Python环境
echo -e "${YELLOW}🔍 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装，请先安装Python3${NC}"
    echo -e "${BLUE}安装命令: sudo apt update && sudo apt install -y python3 python3-pip${NC}"
    exit 1
fi
python3 --version

# 4. 检查Hugo环境
echo -e "${YELLOW}🔍 检查Hugo环境...${NC}"
if ! command -v hugo &> /dev/null; then
    echo -e "${RED}❌ Hugo未安装，请先安装Hugo Extended${NC}"
    echo -e "${YELLOW}💡 自动安装Hugo? (y/N)${NC}"
    read -t 10 -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🔧 自动安装Hugo Extended...${NC}"
        wget -q https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_linux-amd64.deb
        sudo dpkg -i hugo_extended_0.146.0_linux-amd64.deb
        rm hugo_extended_0.146.0_linux-amd64.deb
    else
        exit 1
    fi
fi

HUGO_VERSION=$(hugo version)
if [[ $HUGO_VERSION != *"extended"* ]]; then
    echo -e "${RED}❌ 需要Hugo Extended版本${NC}"
    exit 1
fi
echo -e "${GREEN}✅ $HUGO_VERSION${NC}"

# 5. 检查项目结构
echo -e "${YELLOW}🔍 检查项目结构...${NC}"
if [ ! -f "hugo.toml" ]; then
    echo -e "${RED}❌ hugo.toml配置文件不存在${NC}"
    exit 1
fi

if [ ! -f "scripts/start_separated.py" ]; then
    echo -e "${RED}❌ scripts/start_separated.py启动脚本不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 项目结构检查通过${NC}"

# 6. 端口检查和清理
echo -e "${YELLOW}🔍 检查端口占用...${NC}"
for port in 8000 8080 8081; do
    if command -v ss &> /dev/null; then
        if ss -tulpn | grep -q ":$port "; then
            echo -e "${YELLOW}⚠️  端口 $port 被占用${NC}"
            echo -e "${BLUE}尝试清理端口 $port...${NC}"
            # 尝试友好地停止进程
            pkill -f "port.*$port" 2>/dev/null || true
        fi
    fi
done

# 7. 设置脚本权限
chmod +x scripts/*.py 2>/dev/null || true

# 8. 显示网络信息
echo
echo -e "${BLUE}🌐 网络信息:${NC}"
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "获取失败")
echo -e "${GREEN}WSL2 IP: $WSL_IP${NC}"
echo -e "${GREEN}Windows访问地址: http://localhost:端口号${NC}"

echo
echo -e "${GREEN}🚀 启动Hugo-Self分离式服务架构...${NC}"
echo -e "${YELLOW}⏳ 服务将在以下端口启动:${NC}"
echo -e "  📝 Hugo博客主站: http://localhost:8000"
echo -e "  🛠️  管理后台: http://localhost:8080"  
echo -e "  🔌 API服务器: http://localhost:8081"
echo

# 9. 启动服务 - 增加错误处理
echo -e "${BLUE}🔧 启动服务...${NC}"

# 确保Python可以找到依赖
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"

# 启动服务，捕获输出
if python3 scripts/start_separated.py; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo -e "${YELLOW}💡 尝试手动调试:${NC}"
    echo -e "   python3 scripts/check_services.py"
    echo -e "   python3 -c \"import requests; print(requests.get('http://localhost:8000', timeout=5).status_code)\""
    exit 1
fi

echo
echo -e "${GREEN}🛑 所有服务已停止${NC}"