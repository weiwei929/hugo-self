#!/bin/bash
# WSL2 SSH服务器配置脚本

set -e

echo "🔧 配置WSL2 SSH服务器..."

# 安装SSH服务器
sudo apt update
sudo apt install -y openssh-server

# 配置SSH
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# 修改SSH配置
sudo tee /etc/ssh/sshd_config.d/wsl.conf > /dev/null << 'EOF'
# WSL2 SSH配置
Port 2222
PasswordAuthentication yes
PubkeyAuthentication yes
PermitRootLogin no
X11Forwarding yes
AllowUsers $USER
EOF

# 启动SSH服务
sudo service ssh start

# 获取WSL2 IP地址
WSL_IP=$(hostname -I | awk '{print $1}')

echo "✅ SSH服务器配置完成！"
echo ""
echo "🌐 连接信息："
echo "   SSH地址: $WSL_IP:2222"
echo "   用户名: $USER"
echo "   项目路径: ~/hugo-self"
echo ""
echo "📱 Windows连接命令："
echo "   ssh $USER@$WSL_IP -p 2222"
echo ""
echo "🔧 VS Code SSH连接配置:"
echo "   Host: $WSL_IP"
echo "   Port: 2222"
echo "   User: $USER"

# 创建启动脚本
tee ~/start-hugo-ssh.sh > /dev/null << 'EOF'
#!/bin/bash
# Hugo-Self SSH启动脚本

# 清除代理设置
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY="localhost,127.0.0.1,0.0.0.0,::1"

# 进入项目目录
cd ~/hugo-self

# 启动服务
echo "🚀 启动Hugo-Self服务..."
python3 scripts/start_separated.py
EOF

chmod +x ~/start-hugo-ssh.sh

echo ""
echo "🎯 使用方法："
echo "1. SSH连接到WSL2: ssh $USER@$WSL_IP -p 2222"
echo "2. 运行项目: ~/start-hugo-ssh.sh"
echo "3. 在Windows浏览器访问: http://localhost:端口号"