#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo-Self 端口清理工具
自动检测并清理被占用的端口
"""

import os
import sys
import subprocess
import socket
from pathlib import Path

# Hugo-Self 使用的固定端口
FIXED_PORTS = {
    'hugo': 8000,
    'admin': 8080, 
    'api': 8081
}

def check_port_occupied(port):
    """检查端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.bind(('localhost', port))
            return False  # 端口可用
    except OSError:
        return True  # 端口被占用

def get_process_using_port(port):
    """获取占用端口的进程信息"""
    try:
        result = subprocess.run(
            ["netstat", "-ano", "|", "findstr", f":{port}"],
            shell=True,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        processes = []
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    pid = parts[-1]
                    if pid.isdigit():
                        processes.append(pid)
        
        return list(set(processes))  # 去重
    except Exception as e:
        print(f"获取端口占用信息失败: {e}")
        return []

def get_process_name(pid):
    """根据PID获取进程名称"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            # 第二行包含进程信息
            parts = lines[1].split(',')
            if len(parts) > 0:
                return parts[0].strip('"')
        
        return "未知进程"
    except Exception:
        return "未知进程"

def kill_process(pid, process_name):
    """终止指定PID的进程"""
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/PID", pid],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   ✅ 已终止进程: {process_name} (PID: {pid})")
            return True
        else:
            print(f"   ❌ 终止进程失败: {process_name} (PID: {pid})")
            return False
    except Exception as e:
        print(f"   ❌ 终止进程时出错: {e}")
        return False

def cleanup_ports():
    """清理所有Hugo-Self相关端口"""
    print("🧹 Hugo-Self 端口清理工具")
    print("=" * 50)
    
    occupied_info = []
    
    # 检查所有端口占用情况
    for service, port in FIXED_PORTS.items():
        if check_port_occupied(port):
            pids = get_process_using_port(port)
            occupied_info.append((service, port, pids))
    
    if not occupied_info:
        print("✅ 所有端口都可用，无需清理")
        return True
    
    print("🔍 发现以下端口被占用:")
    print("-" * 50)
    
    all_pids = set()
    for service, port, pids in occupied_info:
        print(f"🔴 {service.upper()} 端口 {port}:")
        for pid in pids:
            process_name = get_process_name(pid)
            print(f"   进程: {process_name} (PID: {pid})")
            all_pids.add((pid, process_name))
    
    if not all_pids:
        print("❌ 未找到占用进程的详细信息")
        return False
    
    print("\n🤔 准备清理以下进程:")
    print("-" * 50)
    for pid, process_name in all_pids:
        print(f"   {process_name} (PID: {pid})")
    
    # 确认清理
    try:
        confirm = input("\n❓ 确定要终止这些进程吗？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return False
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
        return False
    
    print("\n🔥 开始清理进程...")
    print("-" * 50)
    
    success_count = 0
    for pid, process_name in all_pids:
        if kill_process(pid, process_name):
            success_count += 1
    
    print(f"\n📊 清理完成: {success_count}/{len(all_pids)} 个进程被成功终止")
    
    # 重新检查端口状态
    print("\n🔍 验证端口清理结果...")
    print("-" * 50)
    
    all_clear = True
    for service, port in FIXED_PORTS.items():
        if check_port_occupied(port):
            print(f"❌ {service.upper()} 端口 {port} 仍被占用")
            all_clear = False
        else:
            print(f"✅ {service.upper()} 端口 {port} 已释放")
    
    if all_clear:
        print("\n🎉 所有端口清理成功！现在可以启动 Hugo-Self 了")
        print("\n💡 运行以下命令启动服务:")
        print("   cd d:\\Projects\\hugo-self")
        print("   python scripts\\start_separated.py")
    else:
        print("\n⚠️ 部分端口仍被占用，可能需要:")
        print("   1. 重启电脑")
        print("   2. 手动检查并关闭相关程序")
        print("   3. 检查防火墙或安全软件")
    
    return all_clear

def main():
    """主函数"""
    try:
        return 0 if cleanup_ports() else 1
    except KeyboardInterrupt:
        print("\n\n❌ 操作被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 清理过程中出现错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())