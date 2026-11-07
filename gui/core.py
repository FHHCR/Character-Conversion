"""
GUI 核心逻辑模块（不依赖 tkinter）

包含 GUI 界面需要的纯逻辑函数，可独立测试。
"""

import os

from converter.utils import ensure_dir


def validate_output_path(path):
    """
    验证输出路径，不存在则创建

    Args:
        path: 输出目录路径

    Returns:
        bool: 路径是否有效
    """
    try:
        ensure_dir(path)
        return True
    except Exception:
        return False


def generate_output_filename(filename, target_encoding):
    """
    生成输出文件名

    Args:
        filename: 原文件名
        target_encoding: 目标编码

    Returns:
        str: 新文件名
    """
    base, ext = os.path.splitext(filename)
    encoding_label = target_encoding.replace('_', '-')
    return f"{base}_{encoding_label}{ext}"


def is_text_file(file_path):
    """
    判断文件是否为文本文件（启发式检查）

    检查文件内容是否可以被 UTF-8 或 GBK 解码。

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否为文本文件
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read(8192)
        # 尝试解码
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        try:
            content.decode('gbk')
            return True
        except UnicodeDecodeError:
            return False
    except Exception:
        return False


def get_file_info(file_path):
    """
    获取文件信息

    Args:
        file_path: 文件路径

    Returns:
        dict: {'name': str, 'size': int, 'path': str}
    """
    return {
        'name': os.path.basename(file_path),
        'size': os.path.getsize(file_path),
        'path': file_path
    }
