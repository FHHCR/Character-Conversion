"""
工具函数模块

提供文件大小格式化、目录创建、编码检测等工具函数。
"""

import os


def format_size(size_bytes):
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的大小，如 "1.00 KB"
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def ensure_dir(path):
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)


def detect_encoding(file_path):
    """
    检测文件编码（启发式检测）

    尝试按优先级检测文件编码：
    1. 检查 BOM
    2. 尝试 UTF-8
    3. 尝试 GBK

    Args:
        file_path: 文件路径

    Returns:
        str: 检测到的编码
    """
    # 读取文件头部
    with open(file_path, 'rb') as f:
        raw = f.read(4)

    # 检查 BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    if raw.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    if raw.startswith(b'\xfe\xff'):
        return 'utf-16-be'

    # 读取更多内容用于检测
    with open(file_path, 'rb') as f:
        content = f.read(4096)

    # 尝试 UTF-8
    try:
        content.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    # 尝试 GBK
    try:
        content.decode('gbk')
        return 'gbk'
    except UnicodeDecodeError:
        pass

    # 默认返回 UTF-8
    return 'utf-8'
