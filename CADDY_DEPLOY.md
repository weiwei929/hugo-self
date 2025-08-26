# Hugo-Self Caddy 部署指南

本指南介绍如何使用 Caddy 反向代理部署 Hugo-Self 博客。

## 为什么选择 Caddy？

- **自动 HTTPS**：自动申请和续期 Let's Encrypt 证书
- **配置简单**：Caddyfile 语法简洁易懂
- **性能优秀**：内置 HTTP/2、HTTP/3 支持
- **安全默认**：默认启用安全头和最佳实践
- **零停机重载**：配置更新无需重启

## 安装 Caddy

### Ubuntu/Debian

```bash
# 添加 Caddy 官方仓库
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list

# 安装 Caddy
sudo apt update
sudo apt install caddy
```

### CentOS/RHEL

```bash
# 添加 Caddy 仓库
sudo dnf install 'dnf-command(copr)'
sudo dnf copr enable @caddy/caddy
sudo dnf install caddy
```

### 手动安装

```bash
# 下载最新版本
curl -OL "https://github.com/caddyserver/caddy/releases/latest/download/caddy_linux_amd64.tar.gz"
tar -xzf caddy_linux_amd64.tar.gz
sudo mv caddy /usr/local/bin/
sudo chmod +x /usr/local/bin/caddy
```

## 部署步骤

### 1. 准备项目文件

```bash
# 克隆项目到服务器
git clone https://github.com/weiwei929/hugo-self.git
cd hugo-self

# 生成静态文件
hugo --minify

# 创建部署目录
sudo mkdir -p /var/www/hugo-self
sudo cp -r public/* /var/www/hugo-self/
sudo chown -R caddy:caddy /var/www/hugo-self
```

### 2. 配置 Caddyfile

编辑项目根目录的 `Caddyfile`，修改以下配置：

```caddyfile
# 替换为你的域名
yourdomain.com {
    # 替换为实际的网站根目录
    root * /var/www/hugo-self
    
    # 其他配置保持不变...
}
```

### 3. 复制配置文件

```bash
# 复制 Caddyfile 到 Caddy 配置目录
sudo cp Caddyfile /etc/caddy/Caddyfile

# 验证配置文件语法
sudo caddy validate --config /etc/caddy/Caddyfile
```

### 4. 启动 Caddy 服务

```bash
# 启动 Caddy 服务
sudo systemctl start caddy

# 设置开机自启
sudo systemctl enable caddy

# 检查服务状态
sudo systemctl status caddy
```

### 5. 配置防火墙

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 80
sudo ufw allow 443

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 配置说明

### 主要配置项

```caddyfile
yourdomain.com {
    # 网站根目录
    root * /var/www/hugo-self
    
    # 启用文件服务
    file_server
    
    # 启用 gzip 压缩
    encode gzip
    
    # 静态资源缓存（1年）
    @static {
        path *.css *.js *.png *.jpg *.jpeg *.gif *.ico *.svg
    }
    header @static Cache-Control "public, max-age=31536000"
    
    # HTML 文件缓存（1小时）
    @html {
        path *.html
    }
    header @html Cache-Control "public, max-age=3600"
}
```

### 安全配置

```caddyfile
# 安全头设置
header {
    X-Frame-Options "SAMEORIGIN"
    X-Content-Type-Options "nosniff"
    X-XSS-Protection "1; mode=block"
    Referrer-Policy "strict-origin-when-cross-origin"
    Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';"
}
```

### 管理后台保护

```caddyfile
# 管理后台额外安全措施
yourdomain.com/admin/* {
    # IP 白名单（可选）
    @allowed_ips {
        remote_ip 192.168.1.0/24 10.0.0.0/8
    }
    abort @allowed_ips
    
    # 防止搜索引擎索引
    header X-Robots-Tag "noindex, nofollow"
}
```

## 日常维护

### 更新网站内容

```bash
# 进入项目目录
cd /path/to/hugo-self

# 拉取最新代码
git pull origin main

# 重新生成静态文件
hugo --minify

# 更新部署文件
sudo cp -r public/* /var/www/hugo-self/
sudo chown -R caddy:caddy /var/www/hugo-self
```

### 重载配置

```bash
# 重载 Caddy 配置（零停机）
sudo systemctl reload caddy

# 或使用 Caddy 命令
sudo caddy reload --config /etc/caddy/Caddyfile
```

### 查看日志

```bash
# 查看 Caddy 服务日志
sudo journalctl -u caddy -f

# 查看访问日志
sudo tail -f /var/log/caddy/hugo-self.log
```

### 证书管理

```bash
# 查看证书状态
sudo caddy list-certificates

# 手动续期证书（通常自动进行）
sudo caddy renew-certificates
```

## 性能优化

### 启用 HTTP/3

```caddyfile
{
    servers {
        protocol {
            experimental_http3
        }
    }
}
```

### 启用 Brotli 压缩

```caddyfile
yourdomain.com {
    encode {
        gzip
        zstd
    }
}
```

### 预加载关键资源

```caddyfile
@preload {
    path /css/main.css /js/main.js
}
header @preload Link "</css/main.css>; rel=preload; as=style, </js/main.js>; rel=preload; as=script"
```

## 监控和告警

### 健康检查

```caddyfile
yourdomain.com {
    handle /health {
        respond "OK" 200
    }
}
```

### 集成监控系统

可以配合 Prometheus、Grafana 等监控系统：

```bash
# 启用 Caddy 指标端点
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile --with-metrics
```

## 故障排除

### 常见问题

1. **证书申请失败**
   - 检查域名 DNS 解析
   - 确保 80/443 端口开放
   - 查看 Caddy 日志

2. **配置文件错误**
   ```bash
   sudo caddy validate --config /etc/caddy/Caddyfile
   ```

3. **权限问题**
   ```bash
   sudo chown -R caddy:caddy /var/www/hugo-self
   sudo chmod -R 755 /var/www/hugo-self
   ```

4. **服务无法启动**
   ```bash
   sudo journalctl -u caddy --no-pager -l
   ```

## 自动化部署脚本

创建部署脚本 `deploy.sh`：

```bash
#!/bin/bash
set -e

echo "开始部署 Hugo-Self..."

# 拉取最新代码
git pull origin main

# 生成静态文件
hugo --minify

# 备份当前部署
sudo cp -r /var/www/hugo-self /var/www/hugo-self.backup.$(date +%Y%m%d_%H%M%S)

# 部署新文件
sudo cp -r public/* /var/www/hugo-self/
sudo chown -R caddy:caddy /var/www/hugo-self

# 重载 Caddy 配置
sudo systemctl reload caddy

echo "部署完成！"
```

使用方法：
```bash
chmod +x deploy.sh
./deploy.sh
```

## 总结

使用 Caddy 部署 Hugo-Self 的优势：

- ✅ **简单配置**：Caddyfile 语法直观
- ✅ **自动 HTTPS**：无需手动管理证书
- ✅ **高性能**：内置优化和现代协议支持
- ✅ **安全默认**：自动应用安全最佳实践
- ✅ **零停机部署**：配置重载不影响服务

现在您的 Hugo-Self 博客已经可以通过 Caddy 高效、安全地提供服务了！
