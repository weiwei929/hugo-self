#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端口管理工具 - 解决端口冲突问题
"""

import socket
import subprocess
import platform
from typing import List, Tuple, Optional

class PortManager:
    """端口管理器 - 自动检测和分配可用端口"""
    
    # 预设端口池 - 使用更高端口号避免 Windows 权限问题
    DEFAULT_HUGO_PORTS = [8000, 8001, 8002, 3000, 8888, 9090]
    DEFAULT_API_PORTS = [8081, 8082, 8083, 9000, 9001]
    
    @staticmethod
    def is_port_free(port: int, host: str = 'localhost') -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0
        except (socket.error, OSError):
            return False
    
    @staticmethod
    def find_free_port(port_list: List[int], host: str = 'localhost') -> Optional[int]:
        """从端口列表中找到第一个可用端口"""
        for port in port_list:
            if PortManager.is_port_free(port, host):
                return port
        return None
    
    @staticmethod
    def get_random_free_port(start: int = 8000, end: int = 9000) -> Optional[int]:
        """在指定范围内获取随机可用端口"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('', 0))
                port = sock.getsockname()[1]
                if start <= port <= end:
                    return port
                # 如果随机端口不在范围内，则在范围内查找
                for port in range(start, end + 1):
                    if PortManager.is_port_free(port):
                        return port
        except (socket.error, OSError):
            pass
        return None
    
    @staticmethod
    def kill_process_on_port(port: int) -> bool:
        """终止占用指定端口的进程（谨慎使用）"""
        try:
            system = platform.system().lower()
            if system == 'windows':
                # Windows: 查找并终止进程
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(['taskkill', '/F', '/PID', pid], 
                                         capture_output=True)
                            return True
            else:
                # Linux/macOS: 使用lsof和kill
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'], 
                    capture_output=True, 
                    text=True
                )
                if result.stdout.strip():
                    pid = result.stdout.strip()
                    subprocess.run(['kill', '-9', pid], capture_output=True)
                    return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return False
    
    @classmethod
    def get_hugo_port(cls, preferred_port: int = 8000) -> Tuple[int, str]:
        """获取Hugo服务器可用端口"""
        # 先检查首选端口
        if cls.is_port_free(preferred_port):
            return preferred_port, f"使用首选端口 {preferred_port}"
        
        # 从预设端口池中查找
        free_port = cls.find_free_port(cls.DEFAULT_HUGO_PORTS)
        if free_port:
            return free_port, f"从预设端口池选择端口 {free_port}"
        
        # 获取随机端口
        random_port = cls.get_random_free_port(8000, 8999)
        if random_port:
            return random_port, f"分配随机端口 {random_port}"
        
        # 最后尝试终止首选端口的进程（可选）
        print(f"⚠️  警告: 端口 {preferred_port} 被占用")
        choice = input("是否尝试终止占用进程? (y/N): ").lower().strip()
        if choice == 'y':
            if cls.kill_process_on_port(preferred_port):
                if cls.is_port_free(preferred_port):
                    return preferred_port, f"终止进程后使用端口 {preferred_port}"
        
        raise RuntimeError("无法找到可用的Hugo服务器端口")
    
    @classmethod
    def get_api_port(cls, preferred_port: int = 8081) -> Tuple[int, str]:
        """获取API服务器可用端口"""
        # 先检查首选端口
        if cls.is_port_free(preferred_port):
            return preferred_port, f"使用首选端口 {preferred_port}"
        
        # 从预设端口池中查找
        free_port = cls.find_free_port(cls.DEFAULT_API_PORTS)
        if free_port:
            return free_port, f"从预设端口池选择端口 {free_port}"
        
        # 获取随机端口
        random_port = cls.get_random_free_port(9000, 9999)
        if random_port:
            return random_port, f"分配随机端口 {random_port}"
        
        raise RuntimeError("无法找到可用的API服务器端口")
    
    @staticmethod
    def check_port_conflicts() -> dict:
        """检查所有预设端口的占用情况"""
        report = {
            'hugo_ports': {},
            'api_ports': {},
            'conflicts': []
        }
        
        # 检查Hugo端口
        for port in PortManager.DEFAULT_HUGO_PORTS:
            is_free = PortManager.is_port_free(port)
            report['hugo_ports'][port] = 'free' if is_free else 'occupied'
            if not is_free:
                report['conflicts'].append(f"Hugo端口 {port} 被占用")
        
        # 检查API端口
        for port in PortManager.DEFAULT_API_PORTS:
            is_free = PortManager.is_port_free(port)
            report['api_ports'][port] = 'free' if is_free else 'occupied'
            if not is_free:
                report['conflicts'].append(f"API端口 {port} 被占用")
        
        return report

def main():
    """测试端口管理器功能"""
    pm = PortManager()
    
    print("🔍 端口占用情况检查")
    print("=" * 40)
    
    # 检查端口冲突
    report = pm.check_port_conflicts()
    
    print("Hugo端口状态:")
    for port, status in report['hugo_ports'].items():
        status_icon = "✅" if status == 'free' else "❌"
        print(f"  {status_icon} {port}: {status}")
    
    print("\nAPI端口状态:")
    for port, status in report['api_ports'].items():
        status_icon = "✅" if status == 'free' else "❌"
        print(f"  {status_icon} {port}: {status}")
    
    # 获取推荐端口
    try:
        hugo_port, hugo_msg = pm.get_hugo_port()
        print(f"\n🚀 推荐Hugo端口: {hugo_port} ({hugo_msg})")
    except RuntimeError as e:
        print(f"\n❌ Hugo端口分配失败: {e}")
    
    try:
        api_port, api_msg = pm.get_api_port()
        print(f"🔧 推荐API端口: {api_port} ({api_msg})")
    except RuntimeError as e:
        print(f"❌ API端口分配失败: {e}")

if __name__ == "__main__":
    main()