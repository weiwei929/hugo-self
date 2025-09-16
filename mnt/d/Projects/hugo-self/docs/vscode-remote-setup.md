# VS Code Remote-WSL 配置指南

## 🎯 为什么选择VS Code Remote-WSL？

1. **原生WSL2文件系统访问** - 直接在WSL2环境中开发，无跨文件系统性能损失
2. **集成终端** - 直接在WSL2环境中运行命令，无需手动管理代理设置
3. **端口转发** - 自动处理端口映射，Windows可直接访问localhost
4. **环境隔离** - 完全在WSL2环境中运行，避免代理冲突

## 📥 安装步骤

### 1. 安装VS Code扩展
```bash
# 在Windows中安装VS Code
# 安装扩展：Remote - WSL
```

### 2. 在WSL2中准备项目
```bash
# 进入WSL2
wsl

# 迁移项目到WSL2原生文件系统（重要！）
cp -r /mnt/d/Projects/hugo-self ~/hugo-self
cd ~/hugo-self

# 安装依赖
sudo apt update
sudo apt install -y curl git build-essential python3 python3-pip

# 安装Hugo Extended
wget https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_linux-amd64.deb
sudo dpkg -i hugo_extended_0.146.0_linux-amd64.deb

# 验证安装
hugo version
python3 --version
```

### 3. 启动VS Code Remote-WSL
```bash
# 在WSL2项目目录中
cd ~/hugo-self
code .
```

## 🛠️ 优化配置

### 1. WSL2网络优化
创建 `.wslconfig` 文件在 `C:\Users\<username>\.wslconfig`：
```ini
[wsl2]
memory=4GB
processors=2
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true
```

### 2. 清理代理配置
```bash
# 编辑 ~/.bashrc
nano ~/.bashrc

# 确保没有代理设置，如果有则注释掉：
# export http_proxy=...
# export https_proxy=...

# 添加NO_PROXY设置
export NO_PROXY="localhost,127.0.0.1,0.0.0.0,::1"

# 重新加载配置
source ~/.bashrc
```

### 3. 项目启动优化
```bash
# 在WSL2原生文件系统中
cd ~/hugo-self

# 启动服务（无需代理设置）
python3 scripts/start_separated.py
```

## 🌐 访问方式

- **Hugo博客**: http://localhost:8000
- **管理后台**: http://localhost:8080  
- **API服务**: http://localhost:8081

VS Code的端口转发功能会自动将WSL2端口映射到Windows。