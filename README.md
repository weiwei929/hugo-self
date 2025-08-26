## Hugo-Self 博客框架（精简版）

Hugo-Self 是基于 Hugo PaperMod 主题精简而来的个人博客框架，专注于内容呈现、发布与管理。移除了冗余功能，保留了博客的核心价值 —— 优质内容的展示。

[![Hugo](https://img.shields.io/badge/Hugo-0.146.0+-blue.svg)](https://gohugo.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 主要特性

### 🎯 专注内容
- ✅ 移除社交分享、评论、复杂SEO等冗余功能
- ✅ 保留文章展示、归档、搜索等核心功能
- ✅ 界面简洁，突出内容本身

### 📝 内容管理
- ✅ **管理后台**：可视化文档管理界面
- ✅ **批量上传**：拖拽上传多个 Markdown 文件
- ✅ **智能处理**：自动格式化和元数据提取
- ✅ **图片管理**：上传、插入、优化图片资源
- ✅ **实时预览**：编辑时实时预览效果
- ✅ **一键发布**：处理完成后一键发布到网站
- ✅ 兼容 Obsidian、Typora 等主流编辑器
- ✅ 支持标签、分类、目录等组织方式
- ✅ 内置搜索功能，快速定位内容

### 🎨 界面设计
- ✅ 响应式设计，完美适配各种设备
- ✅ 支持明暗主题切换
- ✅ 自定义样式，支持个性化配置
- ✅ 优化的阅读体验

### 🚀 性能优化
- ✅ 基于 Hugo 静态生成，加载速度极快
- ✅ 资源压缩和优化
- ✅ 支持本地预览与生产部署
## 🚀 快速开始

### 1. 环境准备

首先确保已安装 Hugo（版本 >= 0.146.0）：

**Windows:**
```bash
# 使用 Chocolatey
choco install hugo-extended

# 或使用 Scoop
scoop install hugo-extended
```

**macOS:**
```bash
# 使用 Homebrew
brew install hugo
```

**Linux:**
```bash
# 下载二进制文件
wget https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_linux-amd64.tar.gz
```

### 2. 获取项目

```bash
git clone https://github.com/weiwei929/hugo-self.git
cd hugo-self
```

### 3. 启动开发服务器

```bash
# 启动本地服务器（包含草稿）
hugo server -D

# 或者不包含草稿
hugo server
```

访问 http://localhost:1313 查看效果

### 4. 启动管理后台

```bash
# Windows 用户
start_admin.bat

# Linux/macOS 用户
python3 scripts/start_admin.py
```

这将启动：
- Hugo 开发服务器 (http://localhost:1313)
- 管理后台 (http://localhost:1313/admin/login/)
- 登录信息：admin / CHENpengfei186

### 5. 创建内容

**使用管理后台（推荐）**：
1. 登录管理后台
2. 上传 Markdown 文件
3. 处理和编辑内容
4. 一键发布

**传统方式**：
```bash
# 创建新文章
hugo new posts/my-first-post.md

# 编辑文章内容
# 文章会自动包含必要的 Front Matter
```

## 📁 项目结构

```
hugo-self/
├── content/              # 📝 内容目录
│   ├── posts/           # 📄 博客文章
│   ├── _index.md        # 🏠 首页内容
│   ├── archives.md      # 📚 归档页面
│   └── search.md        # 🔍 搜索页面
├── static/              # 🖼️ 静态资源
│   └── images/          # 图片文件
├── layouts/             # 🎨 模板文件
│   ├── _default/        # 默认模板
│   ├── partials/        # 部分模板
│   └── shortcodes/      # 短代码
├── assets/              # 💎 资源文件
│   ├── css/            # 样式文件
│   └── js/             # JavaScript 文件
├── i18n/               # 🌍 国际化文件
├── hugo.toml           # ⚙️ 配置文件
└── README.md           # 📖 说明文档
```

## 📝 内容管理

### 创建文章

1. **手动创建**：在 `content/posts/` 目录下创建 `.md` 文件
2. **使用命令**：`hugo new posts/article-name.md`

### Front Matter 示例

```yaml
---
title: "文章标题"
date: 2025-08-21T15:30:00+08:00
draft: false
tags: ["标签1", "标签2"]
categories: ["分类"]
description: "文章描述"
ShowToc: true
TocOpen: false
---
```

### 图片管理

- **全局图片**：放在 `static/images/` 目录
- **文章图片**：可以使用 Page Bundle 方式组织
- **引用方式**：`![描述](/images/picture.jpg)`

### 编辑器推荐

- **Typora**：所见即所得的 Markdown 编辑器
- **Obsidian**：强大的知识管理工具
- **VS Code**：配合 Markdown 插件使用

## 🚀 部署指南

### 生成静态文件

```bash
# 生产环境构建
hugo --minify

# 构建后的文件在 public/ 目录
```

### 部署选项

#### 1. GitHub Pages
```yaml
# .github/workflows/hugo.yml
name: Deploy Hugo site to Pages
on:
  push:
    branches: ["main"]
# ... (完整配置见项目文档)
```

#### 2. Netlify
- 连接 GitHub 仓库
- 构建命令：`hugo --gc --minify`
- 发布目录：`public`

#### 3. VPS 部署
```bash
# 上传 public/ 目录到服务器
# 配置 Nginx/Apache 指向该目录
```

## 🎨 自定义配置

### 主题配置

编辑 `hugo.toml` 文件：

```toml
[params]
  # 默认主题 (auto, light, dark)
  defaultTheme = "auto"

  # 显示阅读时间
  ShowReadingTime = true

  # 显示目录
  ShowToc = true

  # 首页信息
  [params.homeInfoParams]
    Title = "欢迎来到我的博客"
    Content = "专注于内容展示的精简博客框架"
```

### 自定义样式

在 `assets/css/extended/` 目录下创建 CSS 文件：

```css
/* custom.css */
.post-content {
    line-height: 1.8;
    font-size: 16px;
}
```

### 菜单配置

```toml
[menu]
  [[menu.main]]
    name = "首页"
    url = "/"
    weight = 10
  [[menu.main]]
    name = "归档"
    url = "/archives/"
    weight = 20
```

## 🎯 适用场景

- 📖 **个人博客**：技术分享、生活记录
- 📚 **技术文档**：项目文档、教程整理
- 🧠 **知识库**：学习笔记、资料汇总
- ✍️ **写作平台**：专注内容创作的环境

## 🔧 进阶使用

### 自定义短代码

创建 `layouts/shortcodes/note.html`：

```html
<div class="note {{ .Get 0 }}">
    {{ .Inner | markdownify }}
</div>
```

使用方式：
```markdown
{{< note "info" >}}
这是一个提示信息
{{< /note >}}
```

### 批量导入 Obsidian 笔记

1. 将 Obsidian vault 中的 `.md` 文件复制到 `content/posts/`
2. 批量添加 Front Matter（可使用脚本）
3. 调整图片链接路径

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 📄 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

## 🙏 致谢

- [Hugo](https://gohugo.io/) - 强大的静态网站生成器
- [PaperMod](https://github.com/adityatelange/hugo-PaperMod) - 优秀的 Hugo 主题

---

**如需更多帮助或定制方案，欢迎提交 [Issue](https://github.com/weiwei929/hugo-self/issues) 或联系作者。**
