#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo-Self 服务架构完整性检查与自动修复脚本
检查API中间站(8081)、主站(8000)、admin(8080)之间的交互完整性
并提供自动修复功能
"""

import requests
import socket
import time
import json
import subprocess
import threading
from pathlib import Path
import sys

def check_port_status(host='localhost', port=None):
    """检查端口是否可访问"""
    if port is None:
        return False
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def check_http_service(url, timeout=5):
    """检查HTTP服务状态"""
    try:
        response = requests.get(url, timeout=timeout)
        return {
            'status': response.status_code,
            'accessible': response.status_code == 200,
            'content_length': len(response.content),
            'content_type': response.headers.get('Content-Type', 'unknown')
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': None,
            'accessible': False,
            'error': str(e)
        }

def check_api_endpoints(base_url):
    """检查API端点完整性"""
    endpoints = [
        ('/api/health', 'GET'),
        ('/api/documents', 'GET'),
        ('/api/documents/import', 'POST')
    ]
    
    results = {}
    
    for endpoint, method in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = None
            if method == 'GET':
                response = requests.get(url, timeout=5)
            elif method == 'POST':
                # 测试文档导入API
                test_data = {
                    "filename": "test_check.md",
                    "content": "# 测试文档\n\n这是服务检查测试文档。"
                }
                response = requests.post(
                    url, 
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
            else:
                # 不支持的HTTP方法
                results[endpoint] = {
                    'accessible': False,
                    'error': f'不支持的HTTP方法: {method}'
                }
                continue
            
            if response is not None:
                results[endpoint] = {
                    'status': response.status_code,
                    'accessible': response.status_code in [200, 201],
                    'response_size': len(response.content)
                }
                
                # 尝试解析JSON响应
                try:
                    json_data = response.json()
                    results[endpoint]['json_valid'] = True
                    results[endpoint]['response_type'] = type(json_data).__name__
                except:
                    results[endpoint]['json_valid'] = False
                
        except Exception as e:
            results[endpoint] = {
                'accessible': False,
                'error': str(e)
            }
    
    return results

def check_admin_static_resources(admin_url, hugo_url):
    """检查管理后台静态资源代理"""
    test_resources = [
        '/assets/css/extended/admin.css',
        '/assets/css/core/reset.css',
        '/assets/js/fastsearch.js'
    ]
    
    results = {}
    
    for resource in test_resources:
        # 检查Hugo服务器上的资源
        hugo_resource_url = f"{hugo_url}{resource}"
        hugo_result = check_http_service(hugo_resource_url)
        
        # 检查管理后台代理是否正常
        admin_resource_url = f"{admin_url}{resource}"
        admin_result = check_http_service(admin_resource_url)
        
        results[resource] = {
            'hugo_accessible': hugo_result['accessible'],
            'admin_proxy_accessible': admin_result['accessible'],
            'proxy_working': hugo_result['accessible'] and admin_result['accessible']
        }
    
    return results

def check_cross_service_integration():
    """检查服务间集成"""
    print("🔍 Hugo-Self 服务架构完整性检查")
    print("=" * 60)
    
    # 定义服务配置
    services = {
        'hugo_blog': {'name': 'Hugo博客主站', 'port': 8000, 'url': 'http://localhost:8000'},
        'admin_backend': {'name': '管理后台', 'port': 8080, 'url': 'http://localhost:8080'},
        'api_server': {'name': 'API服务器', 'port': 8081, 'url': 'http://localhost:8081'}
    }
    
    # 1. 端口可用性检查
    print("\n📡 1. 端口可用性检查")
    print("-" * 30)
    
    service_status = {}
    for service_key, config in services.items():
        port_accessible = check_port_status(port=config['port'])
        service_status[service_key] = port_accessible
        
        status_icon = "✅" if port_accessible else "❌"
        print(f"{status_icon} {config['name']}: 端口 {config['port']} {'可访问' if port_accessible else '不可访问'}")
    
    # 2. HTTP服务检查
    print("\n🌐 2. HTTP服务状态检查")
    print("-" * 30)
    
    http_results = {}
    for service_key, config in services.items():
        if service_status[service_key]:
            result = check_http_service(config['url'])
            http_results[service_key] = result
            
            status_icon = "✅" if result['accessible'] else "❌"
            if result['accessible']:
                print(f"{status_icon} {config['name']}: HTTP {result['status']} - {result['content_type']}")
            else:
                print(f"{status_icon} {config['name']}: {result.get('error', '访问失败')}")
        else:
            print(f"⏭️  {config['name']}: 跳过（端口不可访问）")
            http_results[service_key] = {'accessible': False}
    
    # 3. API端点完整性检查
    print("\n🔌 3. API端点完整性检查")
    print("-" * 30)
    
    if service_status['api_server'] and http_results['api_server']['accessible']:
        api_results = check_api_endpoints(services['api_server']['url'])
        
        for endpoint, result in api_results.items():
            status_icon = "✅" if result.get('accessible', False) else "❌"
            if result.get('accessible', False):
                json_status = "JSON✓" if result.get('json_valid', False) else "JSON✗"
                print(f"{status_icon} {endpoint}: HTTP {result['status']} ({json_status})")
            else:
                print(f"{status_icon} {endpoint}: {result.get('error', '不可访问')}")
    else:
        print("⏭️  跳过API检查（API服务器不可访问）")
    
    # 4. 静态资源代理检查
    print("\n📁 4. 静态资源代理检查")
    print("-" * 30)
    
    if (service_status['hugo_blog'] and service_status['admin_backend'] and 
        http_results['hugo_blog']['accessible'] and http_results['admin_backend']['accessible']):
        
        resource_results = check_admin_static_resources(
            services['admin_backend']['url'],
            services['hugo_blog']['url']
        )
        
        for resource, result in resource_results.items():
            proxy_icon = "✅" if result['proxy_working'] else "❌"
            hugo_status = "Hugo✓" if result['hugo_accessible'] else "Hugo✗"
            admin_status = "Admin✓" if result['admin_proxy_accessible'] else "Admin✗"
            print(f"{proxy_icon} {resource}: {hugo_status} | {admin_status}")
    else:
        print("⏭️  跳过静态资源检查（依赖服务不可访问）")
    
    # 5. 服务交互链路检查
    print("\n🔗 5. 服务交互链路检查")
    print("-" * 30)
    
    all_services_up = all(service_status.values()) and all(
        http_results[key]['accessible'] for key in http_results.keys()
    )
    
    if all_services_up:
        print("✅ 所有核心服务正常运行")
        print("✅ Hugo博客主站 ←→ 管理后台：静态资源代理正常")
        print("✅ 管理后台 ←→ API服务器：文档管理API可用")
        print("✅ 完整的服务链路：用户 → 管理后台(8080) → API服务器(8081) → Hugo主站(8000)")
    else:
        missing_services = [
            services[key]['name'] for key, status in service_status.items() 
            if not status or not http_results.get(key, {}).get('accessible', False)
        ]
        print(f"❌ 服务链路不完整，缺失服务：{', '.join(missing_services)}")
    
    # 6. 总体健康状态
    print("\n💊 6. 总体健康状态")
    print("-" * 30)
    
    if all_services_up:
        print("🎉 系统状态：健康")
        print("📝 建议：系统运行正常，可以正常使用管理后台功能")
    else:
        print("⚠️  系统状态：异常")
        print("🔧 建议：请启动所有必需的服务")
        print("   - Hugo博客主站：python scripts/start_separated.py")
        print("   - 或单独启动：hugo server --port 8000")
    
    return all_services_up

def auto_fix_services():
    """自动修复服务"""
    print("\n🪟 开始自动修复...")
    print("-" * 30)
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    fixed_services = []
    
    # 检查并启动Hugo服务
    if not check_port_status(port=8000):
        print("🚀 尝试启动Hugo服务...")
        try:
            process = subprocess.Popen(
                ["hugo", "server", "-D", "--port", "8000", "--bind", "0.0.0.0"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            
            time.sleep(3)
            
            if process.poll() is None and check_port_status(port=8000):
                print("✅ Hugo服务启动成功")
                fixed_services.append('Hugo')
            else:
                print("❌ Hugo服务启动失败")
                
        except Exception as e:
            print(f"❌ 启动Hugo时异常: {e}")
    
    # 检查并启动API服务
    if not check_port_status(port=8081):
        print("🚀 尝试启动API服务...")
        try:
            sys.path.insert(0, str(script_dir))
            from document_manager import DocumentManager, WebAPI
            
            dm = DocumentManager(str(project_root))
            api = WebAPI(dm, port=8081)
            
            def run_api():
                try:
                    api.start_server()
                except Exception as e:
                    print(f"API服务运行异常: {e}")
            
            api_thread = threading.Thread(target=run_api, daemon=True)
            api_thread.start()
            
            time.sleep(3)
            
            if check_port_status(port=8081):
                print("✅ API服务启动成功")
                fixed_services.append('API')
            else:
                print("❌ API服务启动失败")
                
        except Exception as e:
            print(f"❌ 启动API时异常: {e}")
    
    if fixed_services:
        print(f"\n✅ 自动修复完成: {', '.join(fixed_services)}")
        print("🔄 请稍等片刻后重新检查服务状态...")
        return True
    else:
        print("❌ 没有服务需要修复或修复失败")
        return False

def main_with_fix():
    """带修复功能的主函数"""
    try:
        # 第一次检查
        healthy = check_cross_service_integration()
        
        # 如果不健康，询问是否进行自动修复
        if not healthy:
            print("\n" + "="*60)
            choice = input("🪟 是否尝试自动修复服务? (y/N): ").lower().strip()
            
            if choice in ['y', 'yes', '是']:
                if auto_fix_services():
                    print("\n🔄 等待 5 秒后重新检查...")
                    time.sleep(5)
                    
                    print("\n" + "="*60)
                    print("🔍 重新检查服务状态")
                    print("="*60)
                    healthy = check_cross_service_integration()
                    
                    if healthy:
                        print("\n🎉 自动修复成功！系统现在正常运行")
                    else:
                        print("\n⚠️  部分问题仍然存在，可能需要手动干预")
        
        return healthy
        
    except KeyboardInterrupt:
        print("\n👋 检查中断")
        return False
    except Exception as e:
        print(f"\n❌ 检查过程出错: {e}")
        return False

if __name__ == "__main__":
    try:
        # 使用带修复功能的主函数
        healthy = main_with_fix()
        sys.exit(0 if healthy else 1)
    except KeyboardInterrupt:
        print("\n👋 检查结束")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)