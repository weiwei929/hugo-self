#!/bin/bash
# Hugo-Self WSL2 Optimized Launcher

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Hugo-Self WSL2 Optimized Launcher${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# 1. Clear proxy settings
echo -e "${YELLOW}Clearing proxy settings...${NC}"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY="localhost,127.0.0.1,0.0.0.0,::1,*.local"

# Check for proxy variables
for proxy_var in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY; do
    if [[ -n "${!proxy_var}" ]]; then
        echo -e "${YELLOW}Found proxy variable $proxy_var=${!proxy_var}${NC}"
        unset $proxy_var
    fi
done

echo -e "${GREEN}Proxy settings cleared${NC}"

# 2. Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 not installed${NC}"
    exit 1
fi
python3 --version

# 3. Check Hugo
echo -e "${YELLOW}Checking Hugo...${NC}"
if ! command -v hugo &> /dev/null; then
    echo -e "${RED}Hugo not installed${NC}"
    exit 1
fi

HUGO_VERSION=$(hugo version)
if [[ $HUGO_VERSION != *"extended"* ]]; then
    echo -e "${RED}Need Hugo Extended version${NC}"
    exit 1
fi
echo -e "${GREEN}$HUGO_VERSION${NC}"

# 4. Check ports
echo -e "${YELLOW}Checking ports...${NC}"
for port in 8000 8080 8081; do
    if command -v ss &> /dev/null; then
        if ss -tulpn | grep -q ":$port "; then
            echo -e "${YELLOW}Port $port occupied, trying to clear...${NC}"
            pkill -f "port.*$port" 2>/dev/null || true
            sleep 1
        fi
    fi
done

# 5. Network info
echo
echo -e "${BLUE}Network Info:${NC}"
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "Failed")
echo -e "${GREEN}WSL2 IP: $WSL_IP${NC}"
echo -e "${GREEN}Windows Access: http://localhost:PORT${NC}"

echo
echo -e "${GREEN}Starting Hugo-Self Services...${NC}"
echo -e "${YELLOW}Services will start on:${NC}"
echo -e "  Hugo Blog: http://localhost:8000"
echo -e "  Admin Panel: http://localhost:8080"  
echo -e "  API Server: http://localhost:8081"
echo

# 6. Start services
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"
python3 scripts/start_separated.py

echo
echo -e "${GREEN}All services stopped${NC}"