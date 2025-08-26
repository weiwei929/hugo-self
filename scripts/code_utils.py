#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码工具模块 - 消除重复代码，提高代码质量
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from contextlib import contextmanager
import tempfile
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileManager:
    """文件操作管理器 - 统一文件操作，减少重复代码"""
    
    @staticmethod
    @contextmanager
    def safe_file_operation(file_path: Union[str, Path], operation: str = "read"):
        """安全的文件操作上下文管理器"""
        file_path = Path(file_path)
        file_handle = None
        
        try:
            if operation == "read":
                if not file_path.exists():
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                file_handle = open(file_path, 'r', encoding='utf-8')
            elif operation == "write":
                # 确保父目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handle = open(file_path, 'w', encoding='utf-8')
            elif operation == "append":
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handle = open(file_path, 'a', encoding='utf-8')
            else:
                raise ValueError(f"不支持的操作类型: {operation}")
            
            yield file_handle
            
        except UnicodeDecodeError:
            # 尝试其他编码
            if file_handle:
                file_handle.close()
            file_handle = open(file_path, operation[0], encoding='gbk')
            yield file_handle
            
        except Exception as e:
            logger.error(f"文件操作失败 {file_path}: {e}")
            raise
        finally:
            if file_handle:
                file_handle.close()
    
    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Dict:
        """安全读取JSON文件"""
        try:
            with FileManager.safe_file_operation(file_path, "read") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"读取JSON文件失败 {file_path}: {e}")
            return {}
    
    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: Dict, indent: int = 2) -> bool:
        """安全写入JSON文件"""
        try:
            with FileManager.safe_file_operation(file_path, "write") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            logger.error(f"写入JSON文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def read_text_file(file_path: Union[str, Path]) -> str:
        """安全读取文本文件"""
        try:
            with FileManager.safe_file_operation(file_path, "read") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文本文件失败 {file_path}: {e}")
            return ""
    
    @staticmethod
    def write_text_file(file_path: Union[str, Path], content: str) -> bool:
        """安全写入文本文件"""
        try:
            with FileManager.safe_file_operation(file_path, "write") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"写入文本文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def batch_load_json_files(directory: Union[str, Path], pattern: str = "*.json") -> List[Dict]:
        """批量加载JSON文件"""
        directory = Path(directory)
        documents = []
        
        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return documents
        
        for json_file in directory.glob(pattern):
            doc = FileManager.read_json_file(json_file)
            if doc:  # 只添加成功读取的文档
                documents.append(doc)
        
        return documents

class TempFileManager:
    """临时文件管理器 - 统一临时文件处理"""
    
    def __init__(self):
        self._temp_files = []
    
    def create_temp_file(self, content: str, suffix: str = '.md', delete: bool = True) -> str:
        """创建临时文件"""
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix=suffix, 
                delete=delete, 
                encoding='utf-8'
            )
            temp_file.write(content)
            temp_file.flush()
            
            if not delete:
                temp_file.close()
                self._temp_files.append(temp_file.name)
                return temp_file.name
            else:
                file_path = temp_file.name
                temp_file.close()
                return file_path
                
        except Exception as e:
            logger.error(f"创建临时文件失败: {e}")
            raise
    
    def cleanup(self):
        """清理所有临时文件"""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"清理临时文件: {temp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file}: {e}")
        self._temp_files.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

class ValidationManager:
    """验证管理器 - 统一数据验证逻辑"""
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path], 
                          allowed_extensions: Optional[List[str]] = None) -> bool:
        """验证文件路径"""
        file_path = Path(file_path)
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return False
        
        # 检查文件扩展名
        if allowed_extensions:
            if file_path.suffix.lower() not in allowed_extensions:
                logger.warning(f"不支持的文件格式: {file_path.suffix}")
                return False
        
        return True
    
    @staticmethod
    def validate_document_data(doc_data: Dict) -> bool:
        """验证文档数据结构"""
        required_fields = ['id', 'title', 'content', 'status']
        
        for field in required_fields:
            if field not in doc_data:
                logger.warning(f"缺少必需字段: {field}")
                return False
        
        # 验证状态值
        valid_statuses = ['pending', 'processing', 'processed', 'published', 'error']
        if doc_data['status'] not in valid_statuses:
            logger.warning(f"无效的状态值: {doc_data['status']}")
            return False
        
        return True
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """验证端口号"""
        return 1 <= port <= 65535

class ResponseManager:
    """响应管理器 - 统一API响应格式"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "操作成功") -> Dict:
        """成功响应"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def error_response(error: str, code: int = 500, data: Any = None) -> Dict:
        """错误响应"""
        return {
            "success": False,
            "error": error,
            "code": code,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def send_json_response(handler, response_data: Dict, status_code: int = 200):
        """发送JSON响应（用于HTTP处理器）"""
        try:
            handler.send_response(status_code)
            handler.send_header('Content-Type', 'application/json')
            handler.send_header('Access-Control-Allow-Origin', '*')
            handler.end_headers()
            
            response_json = json.dumps(response_data, ensure_ascii=False, indent=2)
            handler.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"发送响应失败: {e}")

class IDGenerator:
    """ID生成器 - 统一ID生成逻辑"""
    
    @staticmethod
    def generate_doc_id(prefix: str = "doc") -> str:
        """生成文档ID"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # 添加随机部分避免冲突
        random_part = hashlib.md5(f"{timestamp}{os.urandom(8)}".encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_part}"
    
    @staticmethod
    def generate_image_id(prefix: str = "img") -> str:
        """生成图片ID"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_part = hashlib.md5(f"{timestamp}{os.urandom(8)}".encode()).hexdigest()[:6]
        return f"{prefix}_{timestamp}_{random_part}"

# 导入time模块
import time

def main():
    """测试工具模块功能"""
    print("🧰 代码工具模块测试")
    print("=" * 40)
    
    # 测试文件管理器
    print("📁 测试文件管理器...")
    test_data = {"test": "data", "timestamp": time.time()}
    test_file = Path("test_file_manager.json")
    
    # 写入测试
    success = FileManager.write_json_file(test_file, test_data)
    print(f"写入测试: {'成功' if success else '失败'}")
    
    # 读取测试
    read_data = FileManager.read_json_file(test_file)
    print(f"读取测试: {'成功' if read_data else '失败'}")
    
    # 清理测试文件
    if test_file.exists():
        test_file.unlink()
    
    # 测试临时文件管理器
    print("\n📄 测试临时文件管理器...")
    with TempFileManager() as temp_manager:
        temp_file = temp_manager.create_temp_file("测试内容", ".md", delete=False)
        print(f"临时文件创建: {temp_file}")
        exists_before = os.path.exists(temp_file)
        # 退出上下文管理器后自动清理
    exists_after = os.path.exists(temp_file)
    print(f"自动清理: {exists_before} -> {exists_after}")
    
    # 测试ID生成器
    print("\n🆔 测试ID生成器...")
    doc_id = IDGenerator.generate_doc_id()
    img_id = IDGenerator.generate_image_id()
    print(f"文档ID: {doc_id}")
    print(f"图片ID: {img_id}")
    
    # 测试验证管理器
    print("\n✅ 测试验证管理器...")
    port_valid = ValidationManager.validate_port(8080)
    port_invalid = ValidationManager.validate_port(70000)
    print(f"端口验证 8080: {port_valid}")
    print(f"端口验证 70000: {port_invalid}")
    
    # 测试响应管理器
    print("\n📊 测试响应管理器...")
    success_resp = ResponseManager.success_response({"test": "data"})
    error_resp = ResponseManager.error_response("测试错误")
    print(f"成功响应: {success_resp['success']}")
    print(f"错误响应: {error_resp['success']}")

if __name__ == "__main__":
    main()