#!/bin/bash
# Hugo-Self WSL2 启动脚本
# 使用分离式服务架构

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Hugo-Self WSL2 启动器 (分离式架构)${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# 检查Python环境
echo -e "${YELLOW}🔍 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装，请先安装Python3${NC}"
    exit 1
fi
python3 --version

# 检查Hugo环境
echo -e "${YELLOW}🔍 检查Hugo环境...${NC}"
if ! command -v hugo &> /dev/null; then
    echo -e "${RED}❌ Hugo未安装，请先安装Hugo Extended${NC}"
    echo -e "${YELLOW}💡 安装提示: 使用install_hugo.sh脚本${NC}"
    exit 1
fi

HUGO_VERSION=$(hugo version)
if [[ $HUGO_VERSION != *"extended"* ]]; then
    echo -e "${RED}❌ 需要Hugo Extended版本${NC}"
    exit 1
fi
echo -e "${GREEN}✅ $HUGO_VERSION${NC}"

# 检查项目结构
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

# 设置脚本权限
chmod +x scripts/*.py

# 显示网络信息
echo
echo -e "${BLUE}🌐 网络信息:${NC}"
WSL_IP=$(hostname -I | awk '{print $1}')
echo -e "${GREEN}WSL2 IP: $WSL_IP${NC}"
echo -e "${GREEN}Windows访问地址: http://localhost:端口号${NC}"

echo
echo -e "${GREEN}🚀 启动Hugo-Self分离式服务架构...${NC}"
echo -e "${YELLOW}⏳ 服务将在以下端口启动:${NC}"
echo -e "  📝 Hugo博客主站: http://localhost:8000"
echo -e "  🛠️  管理后台: http://localhost:8080"  
echo -e "  🔌 API服务器: http://localhost:8081"
echo

# 启动服务
python3 scripts/start_separated.py

echo
echo -e "${GREEN}🛑 所有服务已停止${NC}"