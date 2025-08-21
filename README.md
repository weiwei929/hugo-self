## Hugo-Self 博客框架（精简版）
本项目基于 Hugo PaperMod 主题，已精简为专注内容呈现、发布与管理的个人博客框架，适合 Markdown 文章和图片管理，支持本地与服务器部署。

## 主要特性
- 专注于内容展示，移除社交分享、评论、SEO等冗余功能
- 支持 Markdown 文章与图片的高效管理
- 兼容 Obsidian、Typora 等主流编辑器
- 目录结构清晰，便于分类、标签、归档
- UI 可自定义，支持个性化样式
- 支持本地预览与 VPS 部署
  
## 快速开始

1.安装 Hugo
参考官方文档：https://gohugo.io/getting-started/installing/

2.克隆项目

```
git clone https://github.com/weiwei929/hugo-self.git
cd hugo-self
```

3.启动本地服务

```
hugo server -D
```


访问 http://localhost:1313 查看效果

## 内容管理
- Markdown 文件放在 content/ 目录
- 图片放在 static/images/ 或 content/images/
- 推荐用 Typora/Obsidian 编辑和管理

## 部署到 VPS

1.生成静态文件
```
hugo
```

2.用 Nginx/Apache 指向 public/ 目录即可上线

## 目录结构示例

```
content/         # 文章内容（Markdown）
static/images/   # 图片资源
layouts/         # 模板与页面结构
assets/css/      # 样式文件
```

## 个性化定制
- 可修改 layouts 下模板文件，调整页面结构
- 可编辑 css 下样式文件，定制 UI
- 支持 Front Matter 元数据（title、date、tags、categories、cover 等）

## 适用场景

- 个人博客、技术文档、知识库
- Obsidian/Typora 笔记发布
- 内容管理与归档


如需更多帮助或定制方案，欢迎联系作者或提交 Issue。
