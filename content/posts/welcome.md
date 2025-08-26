---
title: "欢迎使用 Hugo-Self 博客框架"
date: 2025-08-21T15:30:00+08:00
draft: false
tags: ["Hugo", "博客", "教程"]
categories: ["使用指南"]
description: "Hugo-Self 博客框架的介绍和使用指南"
ShowToc: true
TocOpen: false
---

## 欢迎来到 Hugo-Self

Hugo-Self 是一个基于 Hugo PaperMod 主题精简而来的个人博客框架，专注于内容展示和管理。

## 主要特性

### 🎯 专注内容
- 移除了社交分享、评论等冗余功能
- 保留了文章展示的核心功能
- 界面简洁，突出内容本身

### 📝 Markdown 支持
Hugo-Self 完美支持 Markdown 语法，包括：

- **粗体文本**
- *斜体文本*
- `行内代码`
- [链接](https://gohugo.io)

### 代码高亮

支持多种编程语言的代码高亮：

```python
def hello_world():
    print("Hello, Hugo-Self!")
    return "欢迎使用精简博客框架"

# 调用函数
message = hello_world()
```

```javascript
// JavaScript 示例
function createBlog() {
    const blog = {
        name: "Hugo-Self",
        theme: "PaperMod",
        features: ["简洁", "快速", "专注内容"]
    };
    
    return blog;
}

console.log(createBlog());
```

### 📱 响应式设计

Hugo-Self 采用响应式设计，在各种设备上都能完美显示：

- 桌面电脑
- 平板电脑  
- 手机

### 🔍 搜索功能

内置了基于 Fuse.js 的搜索功能，可以快速找到你需要的内容。

### 🏷️ 标签和分类

支持为文章添加标签和分类，方便内容管理和检索。

## 如何使用

### 创建新文章

1. 在 `content/posts/` 目录下创建新的 Markdown 文件
2. 添加 Front Matter 元数据
3. 编写文章内容

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

### 本地预览

```bash
hugo server -D
```

### 生成静态文件

```bash
hugo
```

## 目录结构

```
hugo-self/
├── content/          # 文章内容
│   ├── posts/        # 博客文章
│   ├── _index.md     # 首页内容
│   ├── archives.md   # 归档页面
│   └── search.md     # 搜索页面
├── static/           # 静态资源
│   └── images/       # 图片文件
├── layouts/          # 模板文件
├── assets/           # 样式和脚本
├── i18n/            # 国际化文件
└── hugo.toml        # 配置文件
```

## 自定义配置

你可以通过修改 `hugo.toml` 文件来自定义博客：

- 网站标题和描述
- 菜单配置
- 主题设置
- 功能开关

## 部署

Hugo-Self 生成的是静态网站，可以部署到任何静态网站托管服务：

- GitHub Pages
- Netlify
- Vercel
- 自己的服务器

## 总结

Hugo-Self 是一个专注于内容展示的精简博客框架，它：

> 去除了复杂的功能，保留了博客的本质 —— 专注于内容创作和展示。

希望你能喜欢这个简洁而强大的博客框架！

---

*这是一篇示例文章，展示了 Hugo-Self 的各种功能。你可以删除这篇文章，开始创建自己的内容。*
