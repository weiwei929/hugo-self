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
import socket
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# 固定端口配置
FIXED_PORTS = {
    'hugo': 8000,
    'admin': 8080, 
    'api': 8081
}

# 添加脚本目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from document_manager import DocumentManager, WebAPI
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    print("请确保所需的Python模块都存在")
    sys.exit(1)

def check_port_available(port, service_name):
    """
    检查端口是否可用
    返回: (是否可用, 错误信息)
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.bind(('localhost', port))
            return True, None
    except OSError as e:
        return False, f"{service_name} 端口 {port} 被占用"

def check_all_ports():
    """
    检查所有固定端口是否可用
    返回: (是否全部可用, 占用端口列表)
    """
    occupied_ports = []
    
    for service, port in FIXED_PORTS.items():
        is_available, error_msg = check_port_available(port, service)
        if not is_available:
            occupied_ports.append((service, port, error_msg))
    
    return len(occupied_ports) == 0, occupied_ports

def show_port_conflict_message(occupied_ports):
    """
    显示端口冲突错误信息和解决方案
    """
    print("\n" + "=" * 60)
    print("❌ 端口冲突检测到！")
    print("=" * 60)
    
    for service, port, error_msg in occupied_ports:
        print(f"🔴 {error_msg}")
    
    print("\n📋 解决方案:")
    print("\n1️⃣ 手动关闭占用进程:")
    print("   Windows: 打开任务管理器，结束相关进程")
    print("   或使用命令:")
    
    for service, port, _ in occupied_ports:
        print(f"   netstat -ano | findstr :{port}")
        print(f"   taskkill /PID <PID> /F")
    
    print("\n2️⃣ 使用端口清理工具:")
    print("   cd d:\\Projects\\hugo-self")
    print("   python scripts\\cleanup_ports.py")
    
    print("\n3️⃣ 重启电脑（最简单的方法）")
    
    print("\n⚠️ 注意: Hugo-Self 使用固定端口配置:")
    print(f"   📝 Hugo博客: http://localhost:{FIXED_PORTS['hugo']}")
    print(f"   🔧 管理后台: http://localhost:{FIXED_PORTS['admin']}")
    print(f"   🔌 API服务: http://localhost:{FIXED_PORTS['api']}")
    print("\n💡 请确保这些端口未被其他程序占用！")
    print("=" * 60)

def kill_existing_processes():
    """
    尝试自动终止可能的旧进程
    """
    print("🧹 尝试清理可能的旧进程...")
    
    try:
        # 终止可能的Hugo进程
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "hugo.exe"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ 已终止旧的Hugo进程")
        
        # 终止可能的Python进程（谨慎操作）
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True,
            text=True
        )
        
        if "python.exe" in result.stdout:
            print("   ⚠️ 检测到Python进程运行中，请手动检查是否为Hugo-Self相关进程")
            
    except Exception as e:
        print(f"   ⚠️ 自动清理失败: {e}")
        print("   请手动终止相关进程")

class AdminRequestHandler(SimpleHTTPRequestHandler):
    """自定义的管理后台请求处理器"""
    
    def __init__(self, *args, admin_root=None, hugo_port=8000, **kwargs):
        self.admin_root = admin_root or script_dir.parent
        self.hugo_port = hugo_port
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
        elif parsed_path.path.startswith('/admin/editor/'):
            self.serve_admin_page('editor.html')
        elif parsed_path.path.startswith('/admin/documents/'):
            self.serve_admin_page('documents.html')
        elif parsed_path.path.startswith('/admin/images/'):
            self.serve_admin_page('images.html') 
        elif parsed_path.path.startswith('/admin/process/'):
            self.serve_admin_page('process.html')
        elif parsed_path.path.startswith('/editor/'):
            self.serve_admin_page('editor.html')
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

        # 简单替换Hugo模板语法
        content = content.replace('{{ .Site.Title }}', 'Hugo-Self 管理后台')
        content = content.replace('{{ .Title }}', '管理后台')

        # 移除Hugo资源管道语法
        content = content.replace(
            '{{ $adminCSS := resources.Get "css/extended/admin.css" | resources.Minify }}',
            ''
        )
        content = content.replace('{{ $adminCSS.RelPermalink }}', '')

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
        
        # 使用固定端口
        hugo_port = FIXED_PORTS['hugo']
        print(f"🔧 使用固定端口 {hugo_port}")
        
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
        
        # 使用固定端口
        admin_port = FIXED_PORTS['admin']
        print(f"🔧 使用固定端口 {admin_port} 启动管理后台")
        
        # 创建请求处理器工厂
        def handler_factory(*args, **kwargs):
            return AdminRequestHandler(*args, admin_root=script_dir.parent, hugo_port=FIXED_PORTS['hugo'], **kwargs)
        
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
        
        # 使用固定端口
        api_port = FIXED_PORTS['api']
        print(f"🔧 使用固定端口 {api_port}")
        
        dm = DocumentManager(str(script_dir.parent))
        api = WebAPI(dm, port=api_port)
        
        # 在新线程中启动API服务器
        api_thread = threading.Thread(target=api.start_server, daemon=True)
        api_thread.start()
        
        time.sleep(1)
        
        # 验证API服务器是否正常启动
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{api_port}/api/health", timeout=3)
            print(f"✅ API 服务器已启动: http://localhost:{api_port}")
        except Exception:
            print(f"⚠️ API 服务器启动中，但健康检查失败")
        
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
    
    # 检查端口占用情况
    print("\n" + "=" * 50)
    print("🔌 检查端口占用情况...")
    print("=" * 50)
    
    all_ports_available, occupied_ports = check_all_ports()
    
    if not all_ports_available:
        show_port_conflict_message(occupied_ports)
        
        # 提供选择
        print("\n🤔 请选择解决方案:")
        print("1. 尝试自动清理进程（建议）")
        print("2. 手动关闭占用进程后重新运行")
        print("3. 退出程序")
        
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == '1':
                kill_existing_processes()
                time.sleep(2)
                
                # 重新检查端口
                all_ports_available, occupied_ports = check_all_ports()
                if not all_ports_available:
                    print("\n❌ 自动清理失败，请手动关闭占用进程")
                    return 1
                else:
                    print("\n✅ 端口清理成功，继续启动...")
            
            elif choice == '2':
                print("\n请关闭占用进程后重新运行脚本")
                return 1
            
            elif choice == '3':
                print("\n退出程序")
                return 0
            
            else:
                print("\n无效选择，退出程序")
                return 1
                
        except KeyboardInterrupt:
            print("\n\n用户取消操作")
            return 0
    else:
        print("✅ 所有端口都可用")
    
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
    print("🎉 所有服务已成功启动!")
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
    
    print("\n▶️ 服务正在运行中... 按 Ctrl+C 停止所有服务")
    
    try:
        # 保持服务运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 正在停止所有服务...")
        
        if hugo_process:
            hugo_process.terminate()
            hugo_process.wait()
        
        if admin_server:
            admin_server.shutdown()
        
        print("✅ 所有服务已停止")
        return 0

if __name__ == "__main__":
    sys.exit(main())