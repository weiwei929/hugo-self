#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo-Self 管理后台启动脚本
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
import http.server
import socketserver
import urllib.request
import urllib.error
import re

# 添加脚本目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from document_manager import DocumentManager, WebAPI
from port_manager import PortManager

# 全局变量存储端口信息
_hugo_port = None
_api_port = None
_admin_port = None

class AdminRequestHandler(http.server.BaseHTTPRequestHandler):
    """管理后台请求处理器"""
    
    def __init__(self, *args, **kwargs):
        self.admin_root = script_dir.parent
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET请求处理"""
        try:
            print(f"[调试] 收到GET请求: {self.path}")
            if self.path == '/' or self.path == '/admin/':
                print(f"[调试] 匹配到首页路由，调用serve_admin_page")
                self.serve_admin_page('index.html')
            elif self.path == '/admin/login/' or self.path == '/admin/login' or self.path == '/login/' or self.path == '/login':
                print(f"[调试] 匹配到登录页面路由，调用serve_login_page")
                self.serve_login_page()
            elif self.path == '/admin/documents/' or self.path == '/admin/documents':
                self.serve_admin_page('documents.html')
            elif self.path == '/admin/editor/' or self.path == '/admin/editor':
                self.serve_admin_page('editor.html')
            elif self.path == '/admin/images/' or self.path == '/admin/images':
                self.serve_admin_page('images.html')
            elif self.path == '/admin/process/' or self.path == '/admin/process':
                self.serve_admin_page('process.html')
            elif self.path.startswith('/assets/') or self.path.startswith('/css/'):
                self.proxy_hugo_asset(self.path)
            elif self.path == '/favicon.ico':
                self.send_error(404)  # 忽略favicon请求
            else:
                self.send_error(404)
        except Exception as e:
            print(f"[管理后台] 请求处理错误: {e}")
            self.send_error(500)
    
    def serve_admin_page(self, page_name):
        """服务管理后台页面"""
        try:
            # 统一使用layouts/admin目录
            admin_page_path = self.admin_root / 'layouts' / 'admin' / page_name
            
            if admin_page_path.exists():
                with open(admin_page_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 处理Hugo模板语法
                content = self.process_hugo_template(content)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_error(404, f"Admin page not found: {page_name}")
        except Exception as e:
            print(f"[管理后台] 服务页面错误: {e}")
            self.send_error(500, f"Server error: {e}")

    def serve_login_page(self):
        """专门处理登录页面，不添加任何外部CSS链接"""
        try:
            admin_page_path = Path(__file__).parent.parent / 'layouts' / 'admin' / 'login.html'
            print(f"[调试] 登录页面路径: {admin_page_path}")
            print(f"[调试] 文件是否存在: {admin_page_path.exists()}")

            if admin_page_path.exists():
                with open(admin_page_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                print(f"[调试] 读取的内容长度: {len(content)}")
                print(f"[调试] 内容前100字符: {content[:100]}")

                # 登录页面只做最基本的模板替换，不添加任何CSS链接
                content = content.replace('{{ .Site.Title }}', 'Hugo-Self 管理后台')
                content = content.replace('{{ .Title }}', '登录页面')

                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                print(f"[调试] 登录页面发送成功")
            else:
                print(f"[调试] 登录页面文件不存在")
                self.send_error(404, f"Login page not found")
        except Exception as e:
            print(f"[管理后台] 登录页面错误: {e}")
            self.send_error(500, f"Server error: {e}")

    def process_hugo_template(self, content):
        """处理Hugo模板语法，替换为静态链接"""
        global _hugo_port
        hugo_base_url = f"http://localhost:{_hugo_port or 8000}"

        # 检查是否是登录页面（已经有内联样式，不需要外部CSS）
        if '<style>' in content and 'login-container' in content:
            # 登录页面：只处理基本的模板语法，完全不添加任何CSS链接
            content = content.replace('{{ .Site.Title }}', 'Hugo-Self 管理后台')
            content = content.replace('{{ .Title }}', '登录页面')
            # 确保没有任何CSS链接被添加
            return content

        # 其他页面：正常处理CSS资源链接
        content = content.replace(
            '{{ $adminCSS := resources.Get "css/extended/admin.css" | resources.Minify }}',
            ''
        )
        content = content.replace(
            '{{ $adminCSS.RelPermalink }}',
            f'{hugo_base_url}/assets/css/extended/admin.css'  # 指向Hugo服务器
        )

        # 替换其他常见的Hugo模板语法
        content = content.replace('{{ .Site.Title }}', 'Hugo-Self 管理后台')
        content = content.replace('{{ .Title }}', '管理后台')

        # 处理静态资源链接，指向Hugo服务器
        content = re.sub(
            r'{{ \$\w+\.RelPermalink }}',
            f'{hugo_base_url}/css/',
            content
        )

        # 修复页面中的链接，确保指向正确的管理后台路径
        content = content.replace('href="/', 'href="')
        content = content.replace('href="admin/', 'href="/admin/')
        content = content.replace('href="//', 'href="/')  # 修复双斜杠

        return content
    
    def proxy_hugo_asset(self, asset_path):
        """代理Hugo服务器的静态资源"""
        global _hugo_port
        try:
            hugo_url = f"http://localhost:{_hugo_port or 8000}{asset_path}"
            
            with urllib.request.urlopen(hugo_url, timeout=5) as response:
                content = response.read()
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.end_headers()
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            self.send_error(e.code, str(e))
        except Exception as e:
            print(f"[管理后台] 代理资源错误: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """静默日志输出"""
        pass

def start_hugo_with_port(port):
    """使用指定端口启动Hugo服务器"""
    try:
        print(f"🌐 在端口 {port} 启动 Hugo 服务器...")
        process = subprocess.Popen(
            ["hugo", "server", "-D", "--port", str(port)],
            cwd=script_dir.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 等待启动
        time.sleep(5)
        
        if process.poll() is None:
            print(f"✅ Hugo 服务器已启动: http://localhost:{port}")
            global _hugo_port
            _hugo_port = port
            return process
        else:
            stdout, stderr = process.communicate(timeout=2)
            if stderr:
                print(f"端口 {port} 启动失败: {stderr.strip()}")
            return None
    except Exception as e:
        print(f"端口 {port} 启动异常: {e}")
        return None

def start_hugo_server():
    """启动Hugo开发服务器 - 智能端口管理"""
    try:
        print("🚀 启动 Hugo 开发服务器...")

        # 智能端口分配
        try:
            hugo_port, port_msg = PortManager.get_hugo_port()
            print(f"🔧 {port_msg}")
        except RuntimeError as e:
            print(f"❌ 端口分配失败: {e}")
            return None

        # 首先测试Hugo配置
        print("📋 检查 Hugo 配置...")
        test_result = subprocess.run(
            ["hugo", "config"],
            cwd=script_dir.parent,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'  # 忽略编码错误
        )

        if test_result.returncode != 0:
            print(f"❌ Hugo 配置错误:")
            print(f"stderr: {test_result.stderr}")
            return None

        # 启动服务器
        print(f"🌐 启动服务器在端口 {hugo_port}...")
        process = subprocess.Popen(
            ["hugo", "server", "-D", "--port", str(hugo_port)],
            cwd=script_dir.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='ignore'  # 忽略编码错误
        )

        # 等待服务器启动
        time.sleep(5)  # 增加等待时间

        if process.poll() is None:
            print(f"✅ Hugo 服务器已启动: http://localhost:{hugo_port}")
            # 将端口信息存储在全局变量中，供其他函数使用
            global _hugo_port
            _hugo_port = hugo_port
            return process
        else:
            # 读取错误输出
            try:
                stdout, stderr = process.communicate(timeout=2)
                print(f"❌ Hugo 服务器启动失败")
                if stderr:
                    print(f"错误信息: {stderr.strip()}")
                    # 检查是否是端口占用问题
                    if "bind:" in stderr or "address already in use" in stderr:
                        print(f"⚠️  端口 {hugo_port} 被占用，尝试其他端口...")
                        # 尝试下一个可用端口
                        try:
                            next_port = PortManager.find_free_port([p for p in PortManager.DEFAULT_HUGO_PORTS if p > hugo_port])
                            if next_port:
                                print(f"🔄 重试端口 {next_port}...")
                                return start_hugo_with_port(next_port)
                        except Exception:
                            pass
                if stdout:
                    print(f"输出信息: {stdout.strip()}")
            except subprocess.TimeoutExpired:
                print(f"❌ Hugo 服务器启动失败，进程已退出")
                process.kill()
            return None

    except FileNotFoundError:
        print("❌ 未找到 Hugo 命令，请确保已安装 Hugo")
        return None
    except Exception as e:
        print(f"❌ 启动 Hugo 服务器时出错: {e}")
        return None

def start_api_server():
    """启动API服务器 - 智能端口管理"""
    try:
        print("🔧 启动 API 服务器...")
        
        # 智能端口分配
        try:
            api_port, port_msg = PortManager.get_api_port()
            print(f"🔧 {port_msg}")
        except RuntimeError as e:
            print(f"❌ API端口分配失败: {e}")
            return None
        
        dm = DocumentManager(str(script_dir.parent))
        api = WebAPI(dm, port=api_port)
        
        # 在新线程中启动API服务器
        api_thread = threading.Thread(target=api.start_server, daemon=True)
        api_thread.start()
        
        time.sleep(1)
        print(f"✅ API 服务器已启动: http://localhost:{api_port}")
        # 将端口信息存储在全局变量中
        global _api_port
        _api_port = api_port
        return api_thread
        
    except Exception as e:
        print(f"❌ 启动 API 服务器时出错: {e}")
        return None

def start_admin_server():
    """启动管理后台服务器"""
    try:
        print("🔧 启动管理后台服务器...")
        
        # 获取可用端口
        try:
            admin_port = PortManager.find_free_port([8080, 8888, 9000, 9080, 3000])
            if not admin_port:
                raise RuntimeError("无法找到可用的管理后台端口")
            print(f"🔧 使用管理后台端口 {admin_port}")
        except RuntimeError as e:
            print(f"❌ 管理后台端口分配失败: {e}")
            return None
        
        # 启动管理后台服务器
        def run_admin_server():
            with socketserver.TCPServer(("", admin_port), AdminRequestHandler) as httpd:
                httpd.serve_forever()
        
        admin_thread = threading.Thread(target=run_admin_server, daemon=True)
        admin_thread.start()
        
        time.sleep(1)
        print(f"✅ 管理后台服务器已启动: http://localhost:{admin_port}")
        
        global _admin_port
        _admin_port = admin_port
        return admin_thread
        
    except Exception as e:
        print(f"❌ 启动管理后台服务器时出错: {e}")
        return None

def check_dependencies():
    """检查依赖"""
    print("检查依赖...")
    
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

def open_browser(admin_port):
    """打开浏览器 - 使用管理后台端口"""
    import webbrowser
    time.sleep(2)  # 等待服务器完全启动
    
    try:
        print("🌐 打开管理后台...")
        url = f"http://localhost:{admin_port}/admin/login/"
        webbrowser.open(url)
    except Exception as e:
        print(f"无法自动打开浏览器: {e}")
        print(f"请手动访问: http://localhost:{admin_port}/admin/login/")

def main():
    print("=" * 50)
    print("🚀 Hugo-Self 管理后台启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请解决上述问题后重试")
        return 1
    
    print("\n" + "=" * 50)
    print("启动服务...")
    print("=" * 50)
    
    # 启动Hugo服务器
    hugo_process = start_hugo_server()
    if not hugo_process:
        return 1
    
    # 启动API服务器
    api_thread = start_api_server()
    if not api_thread:
        if hugo_process:
            hugo_process.terminate()
        return 1
    
    # 启动管理后台服务器
    admin_thread = start_admin_server()
    if not admin_thread:
        if hugo_process:
            hugo_process.terminate()
        return 1
    
    # 获取端口信息
    hugo_port = _hugo_port if _hugo_port else 8000
    api_port = _api_port if _api_port else 8081
    admin_port = _admin_port if _admin_port else 8080
    
    print("\n" + "=" * 50)
    print("🎉 所有服务已启动!")
    print("=" * 50)
    print(f"📝 管理后台: http://localhost:{admin_port}/admin/login/")
    print(f"🌐 网站前台: http://localhost:{hugo_port}/")
    print(f"🔧 API 服务: http://localhost:{api_port}/")
    print("=" * 50)
    print("💡 登录信息:")
    print("   用户名: admin")
    print("   密码: CHENpengfei186")
    print("=" * 50)
    print("💡 端口说明:")
    print(f"   Hugo服务器: {hugo_port}")
    print(f"   管理后台: {admin_port}")
    print(f"   API服务器: {api_port}")
    print("=" * 50)
    print("按 Ctrl+C 停止所有服务")
    
    # 自动打开浏览器
    browser_thread = threading.Thread(target=open_browser, args=(admin_port,), daemon=True)
    browser_thread.start()
    
    try:
        # 保持主进程运行
        while True:
            time.sleep(1)
            
            # 检查Hugo进程是否还在运行
            if hugo_process and hugo_process.poll() is not None:
                print("\n❌ Hugo 服务器已停止")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        
        # 停止Hugo服务器
        if hugo_process:
            hugo_process.terminate()
            try:
                hugo_process.wait(timeout=5)
                print("✅ Hugo 服务器已停止")
            except subprocess.TimeoutExpired:
                hugo_process.kill()
                print("🔪 强制停止 Hugo 服务器")
        
        print("✅ 所有服务已停止")
        return 0
    
    return 1

if __name__ == "__main__":
    exit(main())
