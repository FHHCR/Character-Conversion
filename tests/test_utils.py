"""
测试工具函数模块
"""

import os
import pytest

from converter.utils import detect_encoding, format_size, ensure_dir


class TestFormatSize:
    """测试文件大小格式化"""

    def test_format_size_bytes(self):
        """测试文件大小格式化"""
        assert format_size(0) == '0 B'
        assert format_size(512) == '512 B'
        assert format_size(1024) == '1.00 KB'
        assert format_size(1024 * 1024) == '1.00 MB'
        assert format_size(1024 * 1024 * 1024) == '1.00 GB'

    def test_format_size_edge(self):
        """测试文件大小格式化边界"""
        assert format_size(1536) == '1.50 KB'
        assert format_size(1024 * 1024 * 1.5) == '1.50 MB'


class TestEnsureDir:
    """测试目录创建"""

    def test_ensure_dir(self, tmp_path):
        """测试创建目录"""
        target = tmp_path / "new" / "nested" / "dir"
        ensure_dir(str(target))
        assert target.exists()
        assert target.is_dir()

    def test_ensure_dir_existing(self, tmp_path):
        """测试已存在目录"""
        ensure_dir(str(tmp_path))
        assert tmp_path.exists()


class TestDetectEncoding:
    """测试编码检测"""

    def test_detect_encoding_utf8(self, tmp_path):
        """测试检测 UTF-8 编码"""
        test_file = tmp_path / "utf8.txt"
        test_file.write_bytes("测试内容".encode('utf-8'))
        encoding = detect_encoding(str(test_file))
        assert 'utf-8' in encoding.lower()

    def test_detect_encoding_gbk(self, tmp_path):
        """测试检测 GBK 编码"""
        test_file = tmp_path / "gbk.txt"
        test_file.write_bytes("测试内容".encode('gbk'))
        encoding = detect_encoding(str(test_file))
        assert 'gb' in encoding.lower() or 'utf-8' in encoding.lower()

    def test_detect_encoding_bom(self, tmp_path):
        """测试检测带 BOM 的 UTF-8"""
        test_file = tmp_path / "bom.txt"
        test_file.write_bytes(b'\xef\xbb\xbf' + "BOM测试".encode('utf-8'))
        encoding = detect_encoding(str(test_file))
        assert 'utf-8' in encoding.lower()
