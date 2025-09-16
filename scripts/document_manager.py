#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo-Self 文档管理脚本
处理文档导入、格式化、发布等功能
"""

import os
import json
import shutil
import re
import time
from datetime import datetime
from pathlib import Path
import argparse
import hashlib
import base64
from typing import Dict, List, Optional, Union
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_doc_id() -> str:
    """生成文档ID"""
    import uuid
    return f"doc_{int(time.time())}_{str(uuid.uuid4())[:8]}"

def batch_load_json_files(directory: Path) -> List[Dict]:
    """批量加载JSON文件"""
    documents = []
    if not directory.exists():
        return documents
    
    for json_file in directory.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            logger.warning(f"加载文件失败 {json_file}: {e}")
    
    return documents

class DocumentManager:
    def __init__(self, project_root: Union[str, Path] = "."):
        self.project_root = Path(project_root)
        self.admin_dir = self.project_root / "admin"
        self.content_dir = self.project_root / "content"
        self.static_dir = self.project_root / "static"
        
        # 确保目录存在
        self.admin_dir.mkdir(exist_ok=True)
        (self.admin_dir / "pending").mkdir(exist_ok=True)
        (self.admin_dir / "processed").mkdir(exist_ok=True)
        (self.admin_dir / "images").mkdir(exist_ok=True)
        (self.admin_dir / "temp").mkdir(exist_ok=True)
        
        self.content_dir.mkdir(exist_ok=True)
        (self.content_dir / "posts").mkdir(exist_ok=True)
        
        self.static_dir.mkdir(exist_ok=True)
        (self.static_dir / "images").mkdir(exist_ok=True)
        (self.static_dir / "images" / "posts").mkdir(exist_ok=True)

        # 图片管理目录结构
        (self.static_dir / "images" / "documents").mkdir(exist_ok=True)
        (self.static_dir / "images" / "gallery").mkdir(exist_ok=True)
        (self.static_dir / "images" / "gallery" / "photography").mkdir(exist_ok=True)
        (self.static_dir / "images" / "gallery" / "screenshots").mkdir(exist_ok=True)
        (self.static_dir / "images" / "gallery" / "misc").mkdir(exist_ok=True)
        (self.static_dir / "images" / "temp").mkdir(exist_ok=True)

    def upload_image(self, image_data: bytes, filename: str, category: str = "gallery",
                    subcategory: str = "misc", tags: List[str] = None, description: str = "") -> Dict:
        """上传图片到指定分类"""
        import uuid
        from datetime import datetime

        # 生成唯一ID和文件名
        image_id = f"img_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        file_ext = Path(filename).suffix.lower()
        new_filename = f"{image_id}{file_ext}"

        # 确定保存路径
        if category == "documents":
            save_dir = self.static_dir / "images" / "documents"
        elif category == "gallery":
            save_dir = self.static_dir / "images" / "gallery" / subcategory
        else:
            save_dir = self.static_dir / "images" / "temp"

        save_dir.mkdir(parents=True, exist_ok=True)
        image_path = save_dir / new_filename

        # 保存图片文件
        with open(image_path, 'wb') as f:
            f.write(image_data)

        # 创建图片元数据
        image_meta = {
            "id": image_id,
            "filename": filename,
            "stored_filename": new_filename,
            "path": str(image_path.relative_to(self.static_dir)),
            "url": f"/images/{image_path.relative_to(self.static_dir / 'images')}",
            "category": category,
            "subcategory": subcategory,
            "tags": tags or [],
            "description": description,
            "size": len(image_data),
            "upload_time": datetime.now().isoformat(),
            "used_in_documents": []
        }

        # 保存元数据到JSON文件
        meta_file = self.admin_dir / "images" / f"{image_id}.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(image_meta, f, ensure_ascii=False, indent=2)

        logger.info(f"图片上传成功: {filename} -> {new_filename}")
        return image_meta

    def import_document(self, file_path: Union[str, Path], source: str = "manual") -> Dict:
        """导入文档到待处理池"""
        file_path_obj = Path(file_path)
        
        # 验证文件
        if not file_path_obj.exists():
            raise FileNotFoundError(f"文件不存在: {file_path_obj}")
        
        allowed_extensions = ['.md', '.markdown', '.txt']
        if file_path_obj.suffix.lower() not in allowed_extensions:
            raise ValueError(f"不支持的文件类型: {file_path_obj.suffix}")
        
        # 读取文件内容
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            raise ValueError(f"文件内容为空: {file_path_obj}")
        
        # 生成文档ID
        doc_id = generate_doc_id()
        
        # 创建文档元数据
        document = {
            "id": doc_id,
            "filename": file_path_obj.name,
            "title": self._extract_title(content) or file_path_obj.stem,
            "content": content,
            "status": "pending",
            "source": source,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size": len(content.encode('utf-8')),
            "word_count": self._count_words(content),
            "images": [],
            "front_matter": {}
        }
        
        # 保存文档
        pending_file = self.admin_dir / "pending" / f"{doc_id}.json"
        content_file = self.admin_dir / "pending" / f"{doc_id}.md"
        
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文档已导入: {doc_id}")
        return document

    def process_document(self, doc_id: str, metadata: Dict) -> Dict:
        """处理文档，添加Front Matter和格式化"""
        pending_file = self.admin_dir / "pending" / f"{doc_id}.json"
        content_file = self.admin_dir / "pending" / f"{doc_id}.md"
        
        if not pending_file.exists():
            raise FileNotFoundError(f"文档不存在: {doc_id}")
        
        # 加载文档
        with open(pending_file, 'r', encoding='utf-8') as f:
            document = json.load(f)
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新元数据
        document.update(metadata)
        document["status"] = "processed"
        document["processed_at"] = datetime.now().isoformat()
        document["updated_at"] = datetime.now().isoformat()
        
        # 生成Front Matter
        front_matter = self._generate_front_matter(document)
        
        # 处理内容
        processed_content = self._process_content(content, document)
        
        # 组合最终内容
        final_content = front_matter + "\n\n" + processed_content
        document["processed_content"] = final_content
        
        # 保存到已处理目录
        processed_file = self.admin_dir / "processed" / f"{doc_id}.json"
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        processed_content_file = self.admin_dir / "processed" / f"{doc_id}.md"
        with open(processed_content_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # 删除待处理目录中的原文件，避免重复
        try:
            pending_file.unlink()  # 删除JSON文件
            if content_file.exists():
                content_file.unlink()  # 删除MD文件
        except Exception as e:
            logger.warning(f"删除待处理文件时出错: {e}")
        
        print(f"文档已处理: {doc_id}")
        return document

    def publish_document(self, doc_id: str) -> Dict:
        """发布文档到content/posts目录"""
        processed_file = self.admin_dir / "processed" / f"{doc_id}.json"
        content_file = self.admin_dir / "processed" / f"{doc_id}.md"
        
        if not processed_file.exists():
            raise FileNotFoundError(f"已处理文档不存在: {doc_id}")
        
        # 加载文档
        with open(processed_file, 'r', encoding='utf-8') as f:
            document = json.load(f)
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成发布文件名
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_title = re.sub(r'[^\w\s-]', '', document['title']).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{date_str}-{safe_title}.md"
        
        # 发布到posts目录
        publish_file = self.content_dir / "posts" / filename
        with open(publish_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 处理图片
        self._publish_images(document, date_str)
        
        # 更新文档状态
        document["status"] = "published"
        document["published_at"] = datetime.now().isoformat()
        document["published_file"] = str(publish_file.relative_to(self.project_root))
        
        # 保存更新后的元数据
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        print(f"文档已发布: {filename}")
        return document

    def save_document(self, doc_id: str, title: str, content: str) -> Dict:
        """保存文档内容和元数据"""
        # 先在processed目录中查找
        processed_file = self.admin_dir / "processed" / f"{doc_id}.json"
        processed_content_file = self.admin_dir / "processed" / f"{doc_id}.md"
        
        # 如果在processed目录中不存在，在pending目录中查找
        if not processed_file.exists():
            pending_file = self.admin_dir / "pending" / f"{doc_id}.json"
            pending_content_file = self.admin_dir / "pending" / f"{doc_id}.md"
            
            if pending_file.exists():
                # 从 pending 移动到 processed
                with open(pending_file, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                processed_file = self.admin_dir / "processed" / f"{doc_id}.json"
                processed_content_file = self.admin_dir / "processed" / f"{doc_id}.md"
                
                # 删除pending文件
                try:
                    pending_file.unlink()
                    if pending_content_file.exists():
                        pending_content_file.unlink()
                except Exception as e:
                    logger.warning(f"删除pending文件时出错: {e}")
            else:
                # 创建新文档
                document = {
                    "id": doc_id,
                    "filename": f"{doc_id}.md",
                    "title": title,
                    "content": content,
                    "status": "processed",
                    "source": "web_editor",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "size": len(content.encode('utf-8')),
                    "word_count": self._count_words(content),
                    "images": [],
                    "front_matter": {}
                }
        else:
            # 加载现有文档
            with open(processed_file, 'r', encoding='utf-8') as f:
                document = json.load(f)
        
        # 更新文档信息
        document["title"] = title
        document["content"] = content
        document["updated_at"] = datetime.now().isoformat()
        document["size"] = len(content.encode('utf-8'))
        document["word_count"] = self._count_words(content)
        document["status"] = "processed"
        
        # 保存文档元数据
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        # 保存文档内容
        with open(processed_content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文档已保存: {doc_id}")
        return document

    def list_documents(self, status: Optional[str] = None) -> List[Dict]:
        """列出文档 - 优化版本"""
        documents = []
        
        # 扫描待处理文档
        if not status or status == "pending":
            pending_dir = self.admin_dir / "pending"
            pending_docs = batch_load_json_files(pending_dir)
            documents.extend(pending_docs)
        
        # 扫描已处理文档
        if not status or status in ["processed", "published"]:
            processed_dir = self.admin_dir / "processed"
            processed_docs = batch_load_json_files(processed_dir)
            
            # 按状态过滤
            if status:
                processed_docs = [doc for doc in processed_docs if doc.get("status") == status]
            
            documents.extend(processed_docs)
        
        # 按创建时间排序
        documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"找到 {len(documents)} 个文档 (状态: {status or '全部'})")
        return documents

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        deleted = False
        
        # 删除待处理文档
        pending_json = self.admin_dir / "pending" / f"{doc_id}.json"
        pending_md = self.admin_dir / "pending" / f"{doc_id}.md"
        
        if pending_json.exists():
            pending_json.unlink()
            deleted = True
        if pending_md.exists():
            pending_md.unlink()
        
        # 删除已处理文档
        processed_json = self.admin_dir / "processed" / f"{doc_id}.json"
        processed_md = self.admin_dir / "processed" / f"{doc_id}.md"
        
        if processed_json.exists():
            processed_json.unlink()
            deleted = True
        if processed_md.exists():
            processed_md.unlink()
        
        return deleted

    def _extract_title(self, content: str) -> Optional[str]:
        """从内容中提取标题"""
        # 尝试从Front Matter提取
        front_matter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if front_matter_match:
            title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', front_matter_match.group(1))
            if title_match:
                return title_match.group(1).strip()
        
        # 尝试从第一个标题提取
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        
        return None

    def _count_words(self, content: str) -> int:
        """统计字数"""
        # 移除Front Matter
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        # 移除Markdown语法
        content = re.sub(r'[#*`_\[\]()]', '', content)
        # 统计中英文字符
        chinese = re.findall(r'[\u4e00-\u9fa5]', content)
        english = re.findall(r'[a-zA-Z]+', content)
        return len(chinese) + len(' '.join(english).split())

    def _generate_front_matter(self, document: Dict) -> str:
        """生成Front Matter"""
        front_matter = [
            "---",
            f'title: "{document.get("title", "")}"',
            f'date: {document.get("date", datetime.now().isoformat())}',
            f'draft: {str(document.get("draft", False)).lower()}',
            f'tags: {json.dumps(document.get("tags", []), ensure_ascii=False)}',
            f'categories: {json.dumps(document.get("categories", []), ensure_ascii=False)}',
            f'description: "{document.get("description", "")}"',
            "ShowToc: true",
            "TocOpen: false",
            "---"
        ]
        return "\n".join(front_matter)

    def _process_content(self, content: str, document: Dict) -> str:
        """处理内容格式"""
        # 移除原有的Front Matter
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        
        # 处理图片链接
        content = self._process_images(content, document)
        
        # 格式化内容
        content = re.sub(r'\n{3,}', '\n\n', content)  # 移除多余空行
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)  # 移除行尾空格
        
        return content.strip()

    def _process_images(self, content: str, document: Dict) -> str:
        """处理图片"""
        # 这里可以实现图片处理逻辑
        # 比如将base64图片保存为文件，更新图片链接等
        return content

    def _publish_images(self, document: Dict, date_str: str):
        """发布图片到static目录"""
        if not document.get("images"):
            return
        
        date_dir = self.static_dir / "images" / "posts" / date_str.replace('-', '/')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        for image in document["images"]:
            # 处理base64图片
            if image.get("data") and image["data"].startswith("data:image/"):
                try:
                    # 解析base64数据
                    header, data = image["data"].split(",", 1)
                    image_data = base64.b64decode(data)
                    
                    # 生成文件名
                    ext = header.split("/")[1].split(";")[0]
                    filename = f"{image['id']}.{ext}"
                    
                    # 保存图片
                    image_file = date_dir / filename
                    with open(image_file, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"图片已保存: {image_file}")
                    
                except Exception as e:
                    print(f"保存图片失败 {image['id']}: {e}")

    def rebuild_site(self):
        """重新构建Hugo网站"""
        try:
            import subprocess
            result = subprocess.run(["hugo", "--minify"], 
                                  cwd=self.project_root, 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                print("网站重建成功")
                return True
            else:
                print(f"网站重建失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"重建网站时出错: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Hugo-Self 文档管理工具")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 导入命令
    import_parser = subparsers.add_parser("import", help="导入文档")
    import_parser.add_argument("file", help="要导入的文件路径")
    import_parser.add_argument("--source", default="manual", help="文档来源")
    
    # 列表命令
    list_parser = subparsers.add_parser("list", help="列出文档")
    list_parser.add_argument("--status", choices=["pending", "processed", "published"], help="过滤状态")
    
    # 发布命令
    publish_parser = subparsers.add_parser("publish", help="发布文档")
    publish_parser.add_argument("doc_id", help="文档ID")
    
    # 删除命令
    delete_parser = subparsers.add_parser("delete", help="删除文档")
    delete_parser.add_argument("doc_id", help="文档ID")
    
    # 重建命令
    rebuild_parser = subparsers.add_parser("rebuild", help="重建网站")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    dm = DocumentManager(args.project_root)
    
    try:
        if args.command == "import":
            doc = dm.import_document(args.file, args.source)
            print(f"导入成功: {doc['id']}")
            
        elif args.command == "list":
            docs = dm.list_documents(args.status)
            print(f"找到 {len(docs)} 个文档:")
            for doc in docs:
                print(f"  {doc['id']}: {doc['title']} ({doc['status']})")
                
        elif args.command == "publish":
            doc = dm.publish_document(args.doc_id)
            print(f"发布成功: {doc['published_file']}")
            
        elif args.command == "delete":
            if dm.delete_document(args.doc_id):
                print(f"删除成功: {args.doc_id}")
            else:
                print(f"文档不存在: {args.doc_id}")
                
        elif args.command == "rebuild":
            dm.rebuild_site()
            
    except Exception as e:
        print(f"错误: {e}")
        return 1
    
    return 0


class WebAPI:
    """简单的Web API服务器，用于处理前端请求"""

    def __init__(self, document_manager: DocumentManager, port: int = 8081):
        self.dm = document_manager
        self.port = port

    def start_server(self):
        """启动简单的HTTP服务器"""
        document_manager = self.dm  # 为内部类提供引用
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import urllib.parse
            import json
            import tempfile
            import os

            class APIHandler(BaseHTTPRequestHandler):
                def log_message(self, format, *args):
                    """自定义日志格式"""
                    print(f"[API] {format % args}")

                def do_OPTIONS(self):
                    """处理CORS预检请求"""
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()

                def do_GET(self):
                    try:
                        if self.path.startswith('/api/documents/'):
                            # 检查是否是获取单个文档的请求
                            path_parts = self.path.split('/')
                            if len(path_parts) == 4 and path_parts[3]:  # /api/documents/{doc_id}
                                doc_id = path_parts[3]
                                self.handle_get_document(doc_id)
                            else:
                                self.handle_list_documents()
                        elif self.path.startswith('/api/documents'):
                            self.handle_list_documents()
                        elif self.path == '/api/health':
                            self.send_json_response(200, {"status": "ok", "message": "API服务器正常运行"})
                        else:
                            self.send_json_response(404, {"error": "接口不存在"})
                    except Exception as e:
                        print(f"[API] GET请求处理错误: {e}")
                        self.send_json_response(500, {"error": str(e)})

                def do_POST(self):
                    try:
                        if self.path == '/api/documents/import':
                            self.handle_import_document()
                        elif self.path == '/api/documents/save':
                            self.handle_save_document()
                        elif self.path == '/api/documents/publish':
                            self.handle_publish_document()
                        elif self.path == '/api/documents/process':
                            self.handle_process_document()
                        else:
                            self.send_json_response(404, {"error": "接口不存在"})
                    except Exception as e:
                        print(f"[API] POST请求处理错误: {e}")
                        self.send_json_response(500, {"error": str(e)})

                def send_json_response(self, status_code, data):
                    """发送JSON响应"""
                    try:
                        self.send_response(status_code)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        response_data = json.dumps(data, ensure_ascii=False, indent=2)
                        self.wfile.write(response_data.encode('utf-8'))
                    except Exception as e:
                        print(f"[API] 发送响应失败: {e}")

                def handle_list_documents(self):
                    """处理文档列表请求"""
                    try:
                        query = urllib.parse.urlparse(self.path).query
                        params = urllib.parse.parse_qs(query)
                        status = params.get('status', [None])[0]

                        # 获取文档列表
                        docs = document_manager.list_documents(status)
                        
                        self.send_json_response(200, {
                            "success": True,
                            "data": docs,
                            "message": f"找到 {len(docs)} 个文档"
                        })

                    except Exception as e:
                        print(f"[API] 获取文档列表失败: {e}")
                        self.send_json_response(500, {
                            "success": False,
                            "error": f"获取失败: {str(e)}"
                        })

                def handle_get_document(self, doc_id):
                    """处理获取单个文档请求"""
                    try:
                        # 先在processed目录中查找
                        processed_file = document_manager.admin_dir / "processed" / f"{doc_id}.json"
                        content_file = document_manager.admin_dir / "processed" / f"{doc_id}.md"

                        # 如果在processed目录中不存在，在pending目录中查找
                        if not processed_file.exists():
                            processed_file = document_manager.admin_dir / "pending" / f"{doc_id}.json"
                            content_file = document_manager.admin_dir / "pending" / f"{doc_id}.md"

                        if not processed_file.exists():
                            self.send_json_response(404, {
                                "success": False,
                                "error": "文档不存在"
                            })
                            return

                        # 加载文档元数据
                        with open(processed_file, 'r', encoding='utf-8') as f:
                            document = json.load(f)

                        # 加载文档内容
                        if content_file.exists():
                            with open(content_file, 'r', encoding='utf-8') as f:
                                document['content'] = f.read()

                        self.send_json_response(200, {
                            "success": True,
                            "data": document,
                            "message": "文档获取成功"
                        })

                    except Exception as e:
                        print(f"[API] 获取文档失败: {e}")
                        self.send_json_response(500, {
                            "success": False,
                            "error": f"获取失败: {str(e)}"
                        })

                def handle_save_document(self):
                    """处理文档保存请求"""
                    try:
                        # 读取请求体获取文档数据
                        content_length = int(self.headers.get('Content-Length', 0))
                        if content_length == 0:
                            self.send_json_response(400, {
                                "success": False,
                                "error": "请求内容为空"
                            })
                            return

                        post_data = self.rfile.read(content_length)
                        try:
                            data = json.loads(post_data.decode('utf-8'))
                            doc_id = data.get('id')
                            title = data.get('title', '')
                            content = data.get('content', '')
                            
                            if not doc_id:
                                self.send_json_response(400, {
                                    "success": False,
                                    "error": "缺少文档ID"
                                })
                                return
                                
                            if not content:
                                self.send_json_response(400, {
                                    "success": False,
                                    "error": "文档内容不能为空"
                                })
                                return
                                
                        except json.JSONDecodeError as e:
                            self.send_json_response(400, {
                                "success": False,
                                "error": f"无效的JSON数据: {str(e)}"
                            })
                            return
                        
                        # 保存文档
                        doc = document_manager.save_document(doc_id, title, content)
                        
                        self.send_json_response(200, {
                            "success": True,
                            "data": doc,
                            "message": "文档保存成功"
                        })
                        
                    except Exception as e:
                        print(f"[API] 文档保存失败: {e}")
                        self.send_json_response(500, {
                            "success": False,
                            "error": f"保存失败: {str(e)}"
                        })

                def handle_import_document(self):
                    """处理文档导入请求"""
                    try:
                        print(f"[API] 处理文档导入请求")
                        content_length = int(self.headers.get('Content-Length', 0))
                        print(f"[API] Content-Length: {content_length}")
                        if content_length == 0:
                            print(f"[API] 请求内容为空")
                            self.send_json_response(400, {
                                "success": False,
                                "error": "请求内容为空"
                            })
                            return

                        post_data = self.rfile.read(content_length)
                        print(f"[API] 接收到数据: {post_data[:100]}...")  # 只显示前100个字符
                        
                        # 处理JSON格式
                        try:
                            data = json.loads(post_data.decode('utf-8'))
                            filename = data.get('filename', 'document.md')
                            content = data.get('content', '')
                            print(f"[API] 解析数据 - filename: {filename}, content长度: {len(content)}")
                            
                            if not content:
                                print(f"[API] 文档内容为空")
                                self.send_json_response(400, {
                                    "success": False,
                                    "error": "文档内容不能为空"
                                })
                                return
                                
                        except json.JSONDecodeError as e:
                            print(f"[API] JSON解析错误: {e}")
                            self.send_json_response(400, {
                                "success": False,
                                "error": f"无效的JSON数据: {str(e)}"
                            })
                            return
                        
                        # 创建临时文件并导入
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                            temp_file.write(content)
                            temp_file_path = temp_file.name
                        
                        try:
                            doc = document_manager.import_document(temp_file_path, "web_upload")
                            doc['filename'] = filename  # 使用原始文件名
                            
                            self.send_json_response(200, {
                                "success": True,
                                "data": doc,
                                "message": "文档导入成功"
                            })
                        finally:
                            # 清理临时文件
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass
                                
                    except Exception as e:
                        print(f"[API] 文档导入失败: {e}")
                        self.send_json_response(500, {
                            "success": False,
                            "error": f"导入失败: {str(e)}"
                        })

                def handle_process_document(self):
                    """处理文档处理请求"""
                    try:
                        # 读取请求体获取文档ID和元数据
                        content_length = int(self.headers.get('Content-Length', 0))
                        if content_length == 0:
                            self.send_json_response(400, {
                                "success": False,
                                "error": "请求内容为空"
                            })
                            return

                        post_data = self.rfile.read(content_length)
                        try:
                            data = json.loads(post_data.decode('utf-8'))
                            doc_id = data.get('id')
                            if not doc_id:
                                self.send_json_response(400, {
                                    "success": False,
                                    "error": "缺少文档ID"
                                })
                                return
                        except json.JSONDecodeError as e:
                            self.send_json_response(400, {
                                "success": False,
                                "error": f"无效的JSON数据: {str(e)}"
                            })
                            return
                        
                        doc = document_manager.process_document(doc_id, data)
                        
                        self.send_json_response(200, {
                            "success": True,
                            "data": doc,
                            "message": "文档处理成功"
                        })
                        
                    except Exception as e:
                        print(f"[API] 文档处理失败: {e}")
                        self.send_json_response(500, {
                            "success": False,
                            "error": f"处理失败: {str(e)}"
                        })

                def handle_publish_document(self):
                    """处理文档发布请求"""
                    try:
                        # 读取请求体获取文档ID
                        content_length = int(self.headers.get('Content-Length', 0))
                        if content_length == 0:
                            self.send_json_response(400, {
                                "success": False,
                                "error": "请求内容为空"
                            })
                            return

                        post_data = self.rfile.read(content_length)
                        try:
                            data = json.loads(post_data.decode('utf-8'))
                            doc_id = data.get('id')
                            if not doc_id:
                                self.send_json_response(400, {
                                    "success": False,
                                    "error": "缺少文档ID"
                                })
                                return
                        except json.JSONDecodeError as e:
                            self.send_json_response(400, {
                                "success": False,
                                "error": f"无效的JSON数据: {str(e)}"
                            })
                            return
                        
                        doc = document_manager.publish_document(doc_id)
                        
                        self.send_json_response(200, {
                            "success": True,
                            "data": doc,
                            "message": "文档发布成功"
                        })

                    except Exception as e:
                        print(f"[API] 文档发布失败: {e}")
                        self.send_json_response(500, {
                            "success": False,
                            "error": f"发布失败: {str(e)}"
                        })

            server = HTTPServer(('localhost', self.port), APIHandler)

            print(f"✅ API服务器启动在 http://localhost:{self.port}")
            print(f"🔍 健康检查: http://localhost:{self.port}/api/health")
            server.serve_forever()

        except ImportError as e:
            print(f"❌ 无法启动Web服务器，缺少依赖: {e}")
        except Exception as e:
            print(f"❌ 启动API服务器失败: {e}")


if __name__ == "__main__":
    exit(main())
