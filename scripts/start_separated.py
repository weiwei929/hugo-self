#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的管理后台服务器
分离管理后台和Hugo博客服务，解决路由冲突问题
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# 添加脚本目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from document_manager import DocumentManager, WebAPI
    from port_manager import PortManager
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    print("请确保所需的Python模块都存在")
    sys.exit(1)

class AdminRequestHandler(SimpleHTTPRequestHandler):
    """自定义的管理后台请求处理器"""
    
    def __init__(self, *args, admin_root=None, **kwargs):
        self.admin_root = admin_root or script_dir.parent
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # 根路径重定向到登录页面
        if parsed_path.path == '/' or parsed_path.path == '':
            self.send_response(302)
            self.send_header('Location', '/login/')
            self.end_headers()
            return
            
        # 处理管理后台页面
        if parsed_path.path.startswith('/login/'):
            self.serve_admin_page('login.html')
        elif parsed_path.path.startswith('/documents/'):
            self.serve_admin_page('documents.html')
        elif parsed_path.path.startswith('/images/'):
            self.serve_admin_page('images.html') 
        elif parsed_path.path.startswith('/process/'):
            self.serve_admin_page('process.html')
        elif parsed_path.path.startswith('/dashboard/') or parsed_path.path.startswith('/admin/'):
            self.serve_admin_page('index.html')
        # 处理favicon和其他常见请求
        elif parsed_path.path == '/favicon.ico':
            self.send_error(404)  # 简单返回404，避免日志干扰
        # 处理静态资源
        elif parsed_path.path.startswith('/assets/'):
            self.proxy_hugo_asset(parsed_path.path)
        elif parsed_path.path.startswith('/static/'):
            self.proxy_hugo_asset(parsed_path.path)
        else:
            # 处理其他静态资源
            super().do_GET()
    
    def serve_admin_page(self, page_name):
        """服务管理后台页面"""
        try:
            admin_page_path = self.admin_root / 'layouts' / 'admin' / page_name
            if admin_page_path.exists():
                with open(admin_page_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 处理Hugo模板语法，替换为静态资源链接
                content = self.process_hugo_template(content)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_error(404, f"Admin page not found: {page_name}")
        except Exception as e:
            self.send_error(500, f"Server error: {e}")
    
    def process_hugo_template(self, content):
        """处理Hugo模板语法，替换为静态链接"""
        # 替换CSS资源链接
        content = content.replace(
            '{{ $adminCSS := resources.Get "css/extended/admin.css" | resources.Minify }}',
            ''
        )
        content = content.replace(
            '{{ $adminCSS.RelPermalink }}',
            'http://localhost:8000/assets/css/extended/admin.css'  # 指向Hugo服务器
        )
        
        # 替换其他常见的Hugo模板语法
        content = content.replace('{{ .Site.Title }}', 'Hugo-Self 管理后台')
        content = content.replace('{{ .Title }}', '管理后台')
        
        # 处理静态资源链接，指向Hugo服务器
        import re
        # 替换其他可能的资源链接
        content = re.sub(
            r'{{ \$\w+\.RelPermalink }}',
            'http://localhost:8000/assets/',
            content
        )
        
        # 修复页面中的链接，确保指向正确的管理后台路径
        content = content.replace('href="/', 'href="')
        content = content.replace('href="admin/', 'href="/admin/')
        content = content.replace('href="//', 'href="/')  # 修复双斜杠
        
        return content
    
    def serve_static_asset(self, asset_path):
        """服务静态资源文件"""
        try:
            # 移除前导斜杠
            if asset_path.startswith('/'):
                asset_path = asset_path[1:]
            
            file_path = self.admin_root / asset_path
            
            if file_path.exists() and file_path.is_file():
                # 检测文件类型
                content_type = self.guess_content_type(str(file_path))
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, f"Static asset not found: {asset_path}")
        except Exception as e:
            self.send_error(500, f"Error serving static asset: {e}")
    
    def guess_content_type(self, file_path):
        """根据文件扩展名猜测内容类型"""
        if file_path.endswith('.css'):
            return 'text/css'
        elif file_path.endswith('.js'):
            return 'application/javascript'
        elif file_path.endswith('.png'):
            return 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            return 'image/jpeg'
        elif file_path.endswith('.gif'):
            return 'image/gif'
        elif file_path.endswith('.svg'):
            return 'image/svg+xml'
        else:
            return 'application/octet-stream'
    
    def proxy_hugo_asset(self, asset_path):
        """代理Hugo服务器的静态资源"""
        try:
            import urllib.request
            import urllib.error
            
            # 构建 Hugo 服务器的 URL
            hugo_url = f"http://localhost:8000{asset_path}"
            
            # 从 Hugo 服务器获取资源
            try:
                with urllib.request.urlopen(hugo_url) as response:
                    content = response.read()
                    content_type = response.headers.get('Content-Type', 'application/octet-stream')
                    
                    self.send_response(200)
                    self.send_header('Content-type', content_type)
                    self.end_headers()
                    self.wfile.write(content)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # 如果Hugo服务器上没有，尝试本地文件
                    self.serve_static_asset(asset_path)
                else:
                    self.send_error(e.code, f"Hugo server error: {e.reason}")
            except Exception as e:
                # 如果无法连接Hugo服务器，尝试本地文件
                self.serve_static_asset(asset_path)
                
        except Exception as e:
            self.send_error(500, f"Error proxying asset: {e}")

def start_hugo_blog():
    """启动Hugo博客服务器"""
    try:
        print("🚀 启动 Hugo 博客服务器...")
        
        # 获取可用端口
        hugo_port, port_msg = PortManager.get_hugo_port()
        print(f"🔧 {port_msg}")
        
        print(f"🌐 启动博客服务器在端口 {hugo_port}...")
        process = subprocess.Popen(
            ["hugo", "server", "-D", "--port", str(hugo_port), "--bind", "0.0.0.0"],
            cwd=script_dir.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 等待启动
        time.sleep(3)
        
        # 检查进程状态
        if process.poll() is None:
            # 进程仍在运行，进一步验证服务器是否真正启动
            import socket
            
            # 尝试连接验证
            for attempt in range(10):  # 最多尝试10次
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', hugo_port))
                        if result == 0:
                            print(f"✅ Hugo 博客服务器已启动: http://localhost:{hugo_port}")
                            return process, hugo_port
                except:
                    pass
                time.sleep(0.5)
            
            # 如果连接失败，检查进程是否还在运行
            if process.poll() is None:
                print(f"⚠️ Hugo 进程运行中但端口 {hugo_port} 无法连接")
                # 读取输出看看有什么错误
                try:
                    process.terminate()
                    stdout, stderr = process.communicate(timeout=5)
                    if stderr:
                        print(f"Hugo 错误输出: {stderr.strip()}")
                    if stdout:
                        print(f"Hugo 标准输出: {stdout.strip()}")
                except:
                    pass
            
            return None, None
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Hugo 博客服务器启动失败")
            if stderr:
                print(f"错误信息: {stderr.strip()}")
            if stdout:
                print(f"输出信息: {stdout.strip()}")
            return None, None
            
    except Exception as e:
        print(f"❌ 启动 Hugo 博客服务器时出错: {e}")
        return None, None

def start_admin_server():
    """启动独立的管理后台服务器"""
    try:
        print("🔧 启动独立管理后台服务器...")
        
        # 获取可用端口
        admin_ports = [8080, 8088, 8090, 9000, 9001]
        admin_port = PortManager.find_free_port(admin_ports)
        if not admin_port:
            admin_port = PortManager.get_random_free_port(9000, 9999)
        
        if not admin_port:
            raise RuntimeError("无法找到可用的管理后台端口")
        
        print(f"🔧 使用端口 {admin_port} 启动管理后台")
        
        # 创建请求处理器工厂
        def handler_factory(*args, **kwargs):
            return AdminRequestHandler(*args, admin_root=script_dir.parent, **kwargs)
        
        # 创建HTTP服务器
        server = HTTPServer(('localhost', admin_port), handler_factory)
        
        # 在新线程中运行服务器
        server_thread = threading.Thread(
            target=server.serve_forever, 
            daemon=True
        )
        server_thread.start()
        
        print(f"✅ 管理后台服务器已启动: http://localhost:{admin_port}")
        return server, admin_port
        
    except Exception as e:
        print(f"❌ 启动管理后台服务器时出错: {e}")
        return None, None

def start_api_server():
    """启动API服务器"""
    try:
        print("🔧 启动 API 服务器...")
        
        # 获取可用端口
        api_port, port_msg = PortManager.get_api_port()
        print(f"🔧 {port_msg}")
        
        dm = DocumentManager(str(script_dir.parent))
        api = WebAPI(dm, port=api_port)
        
        # 在新线程中启动API服务器
        api_thread = threading.Thread(target=api.start_server, daemon=True)
        api_thread.start()
        
        time.sleep(1)
        print(f"✅ API 服务器已启动: http://localhost:{api_port}")
        return api_thread, api_port
        
    except Exception as e:
        print(f"❌ 启动 API 服务器时出错: {e}")
        return None, None

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    # 检查Hugo
    try:
        result = subprocess.run(
            ["hugo", "version"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            print(f"✅ Hugo: {result.stdout.strip()}")
        else:
            print("❌ Hugo 未正确安装")
            return False
    except FileNotFoundError:
        print("❌ 未找到 Hugo 命令")
        return False
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要 Python 3.6 或更高版本")
        return False
    else:
        print(f"✅ Python: {sys.version}")
    
    # 检查项目结构
    project_root = script_dir.parent
    required_dirs = ["content", "layouts", "static", "assets"]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ 目录存在: {dir_name}")
        else:
            print(f"❌ 目录缺失: {dir_name}")
            return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Hugo-Self 分离式启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请解决上述问题后重试")
        return 1
    
    print("\n" + "=" * 50)
    print("启动服务...")
    print("=" * 50)
    
    # 启动Hugo博客服务器
    hugo_process, hugo_port = start_hugo_blog()
    if not hugo_process:
        return 1
    
    # 启动独立管理后台服务器
    admin_server, admin_port = start_admin_server()
    if not admin_server:
        if hugo_process:
            hugo_process.terminate()
        return 1
    
    # 启动API服务器
    api_thread, api_port = start_api_server()
    if not api_thread:
        if hugo_process:
            hugo_process.terminate()
        if admin_server:
            admin_server.shutdown()
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 所有服务已启动!")
    print("=" * 50)
    print(f"📝 博客网站: http://localhost:{hugo_port}/")
    print(f"🔧 管理后台: http://localhost:{admin_port}/")
    print(f"🔌 API 服务: http://localhost:{api_port}/")
    print("=" * 50)
    print("💡 管理后台登录信息:")
    print("   用户名: admin")
    print("   密码: CHENpengfei186")
    print("=" * 50)
    
    # 打开浏览器
    try:
        print("🌐 打开浏览器...")
        time.sleep(2)
        webbrowser.open(f"http://localhost:{admin_port}/")
        webbrowser.open(f"http://localhost:{hugo_port}/")
    except Exception as e:
        print(f"无法自动打开浏览器: {e}")
    
    print("\n按 Ctrl+C 停止所有服务...")
    
    try:
        # 保持服务运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ 正在停止服务...")
        
        if hugo_process:
            hugo_process.terminate()
            hugo_process.wait()
        
        if admin_server:
            admin_server.shutdown()
        
        print("✅ 所有服务已停止")
        return 0

if __name__ == "__main__":
    sys.exit(main())