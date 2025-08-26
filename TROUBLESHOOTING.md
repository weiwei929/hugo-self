# Hugo-Self 故障排除指南

## 问题：无法访问管理后台 (localhost 拒绝连接)

### 可能原因和解决方案

#### 1. Hugo 服务器未正确启动

**症状**：浏览器显示"localhost 拒绝连接"

**解决方案**：
```bash
# 方法1：直接启动Hugo（推荐用于调试）
start_hugo_only.bat

# 方法2：手动启动
hugo server -D --bind 0.0.0.0 --port 1313 --verbose
```

**检查步骤**：
1. 确认Hugo版本：`hugo version`
2. 检查配置：`hugo config`
3. 测试构建：`hugo --minify`

#### 2. 端口被占用

**检查端口占用**：
```bash
# Windows
netstat -ano | findstr :1313

# 如果端口被占用，使用其他端口
hugo server -D --port 1314
```

#### 3. 防火墙阻止

**Windows防火墙**：
1. 打开 Windows Defender 防火墙
2. 点击"允许应用或功能通过 Windows Defender 防火墙"
3. 添加 Hugo 到允许列表

#### 4. Hugo 配置问题

**检查 hugo.toml**：
```toml
baseURL = "http://localhost:1313"  # 确保使用正确的本地地址
languageCode = "zh-cn"
title = "Hugo-Self 博客"
# theme = "PaperMod"  # 确保已注释掉
```

## 问题：管理后台页面显示404

### 解决方案

#### 1. 检查内容文件

确认以下文件存在：
- `content/admin/login.md`
- `content/admin/_index.md`
- `content/admin/documents.md`
- `content/admin/process.md`

#### 2. 检查模板文件

确认以下模板存在：
- `layouts/admin/login.html`
- `layouts/admin/index.html`
- `layouts/admin/documents.html`
- `layouts/admin/process.html`

#### 3. 重新构建

```bash
# 清理并重新构建
hugo --cleanDestinationDir
hugo server -D
```

## 问题：Python 脚本启动失败

### 解决方案

#### 1. 检查 Python 版本

```bash
python --version
# 需要 Python 3.6 或更高版本
```

#### 2. 检查脚本路径

确保在项目根目录运行：
```bash
# 当前目录应该包含 hugo.toml 文件
dir hugo.toml  # Windows
ls hugo.toml   # Linux/macOS
```

#### 3. 手动运行脚本

```bash
python scripts/start_admin.py
```

## 问题：编码错误或乱码

### 解决方案

#### 1. 设置正确的编码

```bash
# Windows 命令行
chcp 65001
```

#### 2. 使用英文版启动脚本

使用 `start_hugo_only.bat` 避免中文编码问题。

## 问题：权限错误

### 解决方案

#### 1. 以管理员身份运行

右键点击命令提示符，选择"以管理员身份运行"

#### 2. 检查文件权限

确保对项目目录有读写权限。

## 调试步骤

### 1. 基础检查

```bash
# 检查Hugo版本
hugo version

# 检查Python版本  
python --version

# 检查当前目录
dir  # Windows
ls   # Linux/macOS
```

### 2. 测试Hugo

```bash
# 测试配置
hugo config

# 测试构建
hugo --minify

# 启动服务器（详细输出）
hugo server -D --verbose
```

### 3. 测试页面访问

1. 启动Hugo服务器
2. 访问测试页面：http://localhost:1313/test/
3. 如果测试页面正常，再访问：http://localhost:1313/admin/login/

### 4. 检查日志

Hugo服务器会在控制台输出详细日志，注意查看：
- 错误信息（ERROR）
- 警告信息（WARN）
- 页面构建信息

## 常见错误信息

### "template not found"
- 检查模板文件是否存在
- 检查模板路径是否正确

### "content file not found"
- 检查内容文件是否存在
- 检查Front Matter格式是否正确

### "port already in use"
- 更换端口：`hugo server -D --port 1314`
- 或关闭占用端口的程序

### "permission denied"
- 以管理员身份运行
- 检查文件权限

## 获取帮助

如果以上方法都无法解决问题：

1. **查看Hugo官方文档**：https://gohugo.io/troubleshooting/
2. **检查项目Issues**：https://github.com/weiwei929/hugo-self/issues
3. **提供详细信息**：
   - 操作系统版本
   - Hugo版本
   - Python版本
   - 完整的错误日志
   - 执行的具体步骤

## 快速修复命令

```bash
# 一键重置和启动
hugo --cleanDestinationDir
hugo server -D --bind 0.0.0.0 --port 1313 --verbose
```

如果仍然无法解决，请尝试使用最简单的方式：

```bash
# 最简启动方式
hugo server -D
```

然后访问：http://localhost:1313/admin/login/
