# Hugo-Self 安装和使用指南

## 系统要求

- Hugo >= 0.146.0 (推荐使用 Extended 版本)
- Git (用于克隆项目)
- 文本编辑器 (推荐 VS Code, Typora, Obsidian)

## 详细安装步骤

### 1. 安装 Hugo

#### Windows

**方法一：使用 Chocolatey (推荐)**
```powershell
# 安装 Chocolatey (如果未安装)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装 Hugo Extended
choco install hugo-extended -y
```

**方法二：使用 Scoop**
```powershell
# 安装 Scoop (如果未安装)
iwr -useb get.scoop.sh | iex

# 安装 Hugo Extended
scoop install hugo-extended
```

**方法三：手动安装**
1. 访问 [Hugo Releases](https://github.com/gohugoio/hugo/releases)
2. 下载 `hugo_extended_x.x.x_windows-amd64.zip`
3. 解压到 `C:\Hugo\bin`
4. 将 `C:\Hugo\bin` 添加到系统 PATH

#### macOS

**使用 Homebrew (推荐)**
```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Hugo
brew install hugo
```

#### Linux

**Ubuntu/Debian:**
```bash
# 下载最新版本
wget https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_linux-amd64.deb

# 安装
sudo dpkg -i hugo_extended_0.146.0_linux-amd64.deb
```

**CentOS/RHEL:**
```bash
# 下载并安装
wget https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_linux-amd64.tar.gz
tar -xzf hugo_extended_0.146.0_linux-amd64.tar.gz
sudo mv hugo /usr/local/bin/
```

### 2. 验证安装

```bash
hugo version
```

应该看到类似输出：
```
hugo v0.146.0+extended linux/amd64 BuildDate=2024-xx-xx
```

### 3. 获取项目

```bash
# 克隆项目
git clone https://github.com/weiwei929/hugo-self.git

# 进入项目目录
cd hugo-self

# 查看项目结构
ls -la
```

## 首次运行

### 方法一：使用管理后台启动器（推荐）

```bash
# Windows 用户
start_admin.bat

# Linux/macOS 用户
python3 scripts/start_admin.py
```

这将自动启动：
- Hugo 开发服务器 (http://localhost:8000)
- 管理后台 (http://localhost:8080)
- API 服务器 (http://localhost:8081)
- 自动打开管理登录页面

### 方法二：手动启动

```bash
# 启动服务器（包含草稿）
hugo server -D

# 或者不包含草稿
hugo server
```

### 2. 访问网站

**前台网站**：http://localhost:8000
- 首页欢迎信息
- 3篇示例文章
- 导航菜单（首页、归档、标签、分类、搜索）

**管理后台**：http://localhost:8080/login/
- 用户名：`admin`
- 密码：`CHENpengfei186`

### 3. 测试功能

**前台功能**：
- **浏览文章**：点击文章标题查看详情
- **查看归档**：访问 `/archives/` 查看所有文章
- **搜索功能**：访问 `/search/` 测试搜索
- **标签分类**：点击文章标签查看相关文章
- **主题切换**：点击右上角的主题切换按钮

**管理后台功能**：
- **文档上传**：批量上传 Markdown 文件
- **文档处理**：编辑、格式化、添加元数据
- **图片管理**：上传和管理图片资源
- **内容发布**：一键发布到网站

## 使用管理后台

### 1. 登录管理后台

访问 http://localhost:8080/login/
- 用户名：`admin`
- 密码：`CHENpengfei186`

### 2. 文档管理工作流程

#### 步骤1：上传文档
1. 进入"文档管理"页面
2. 将 Markdown 文件拖拽到上传区域
3. 或点击"选择文件"批量上传
4. 支持 `.md`, `.markdown`, `.txt` 格式

#### 步骤2：处理文档
1. 在文档列表中点击"处理"按钮
2. 编辑文章标题、分类、标签
3. 添加文章描述和发布日期
4. 上传和插入图片
5. 实时预览效果
6. 点击"保存"完成处理

#### 步骤3：发布文档
1. 在处理页面点击"发布"
2. 或在文档列表中批量发布
3. 文档将自动移动到 `content/posts/` 目录
4. 网站自动重新构建

### 3. 图片管理

- **上传图片**：在文档处理页面上传图片
- **插入图片**：点击图片上的"📝"按钮插入到内容中
- **图片优化**：自动压缩和格式化图片
- **路径管理**：自动处理图片路径和引用

### 4. 传统方式创建文章

如果不使用管理后台，也可以传统方式创建：

```bash
hugo new posts/my-first-post.md
```

编辑 `content/posts/my-first-post.md`：

```markdown
---
title: "我的第一篇文章"
date: 2025-08-21T16:00:00+08:00
draft: false
tags: ["测试", "第一篇"]
categories: ["日记"]
description: "这是我的第一篇文章"
ShowToc: true
TocOpen: false
---

## 欢迎

这是我使用 Hugo-Self 创建的第一篇文章！

### 功能测试

- **粗体文本**
- *斜体文本*
- `行内代码`

### 代码块

```python
print("Hello, Hugo-Self!")
```

### 列表

1. 第一项
2. 第二项
3. 第三项

### 引用

> 这是一个引用块。

### 链接

[Hugo 官网](https://gohugo.io)
```

## 自定义配置

### 1. 修改网站信息

编辑 `hugo.toml`：

```toml
baseURL = "https://yourdomain.com"
title = "我的博客"
languageCode = "zh-cn"

[params]
  description = "这是我的个人博客"
  author = "你的名字"
  
  [params.homeInfoParams]
    Title = "欢迎来到我的博客"
    Content = "分享技术、记录生活"
```

### 2. 自定义菜单

```toml
[menu]
  [[menu.main]]
    name = "首页"
    url = "/"
    weight = 10
  [[menu.main]]
    name = "关于"
    url = "/about/"
    weight = 50
```

### 3. 添加关于页面

```bash
# 创建关于页面
hugo new about.md
```

编辑 `content/about.md`：

```markdown
---
title: "关于我"
date: 2025-08-21T16:00:00+08:00
draft: false
---

## 关于我

这里是关于我的介绍...
```

## 部署到生产环境

### 1. 生成静态文件

```bash
# 生产环境构建
hugo --minify

# 文件生成在 public/ 目录
ls public/
```

### 2. 部署到服务器

```bash
# 上传 public/ 目录到服务器
rsync -avz public/ user@server:/var/www/html/

# 或使用 SCP
scp -r public/* user@server:/var/www/html/
```

### 3. 配置 Web 服务器

**Nginx 配置示例：**

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

## 常见问题

### Q: Hugo 命令找不到？
A: 确保 Hugo 已正确安装并添加到 PATH 环境变量。

### Q: 网站无法访问？
A: 检查防火墙设置，确保 8000、8080、8081 端口未被占用。

### Q: 文章不显示？
A: 检查文章的 `draft` 状态，确保为 `false` 或使用 `-D` 参数。

### Q: 样式不正确？
A: 清除浏览器缓存，或检查 CSS 文件是否正确加载。

### Q: 中文显示乱码？
A: 确保文件编码为 UTF-8。

## 获取帮助

- **项目文档**：查看 README.md
- **示例文章**：参考 `content/posts/` 中的示例
- **问题反馈**：提交 [GitHub Issue](https://github.com/weiwei929/hugo-self/issues)
- **社区支持**：[Hugo 官方论坛](https://discourse.gohugo.io/)

---

**祝你使用愉快！开始你的博客之旅吧！** 🚀
