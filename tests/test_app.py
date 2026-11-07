"""
测试 GUI 核心逻辑（不依赖显示环境）
"""

import os
import sys

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from gui.core import validate_output_path, generate_output_filename, is_text_file, get_file_info


class TestValidateOutputPath:
    """测试输出路径验证"""

    def test_validate_output_path_creates_dir(self, tmp_path):
        """测试创建输出目录"""
        target = tmp_path / "output" / "nested"
        result = validate_output_path(str(target))
        assert result is True
        assert target.exists()

    def test_validate_output_path_existing(self, tmp_path):
        """测试已存在目录"""
        result = validate_output_path(str(tmp_path))
        assert result is True


class TestGenerateOutputFilename:
    """测试输出文件名生成"""

    def test_generate_output_filename(self):
        """测试带扩展名的文件名"""
        assert generate_output_filename("test.txt", "utf-8") == "test_utf-8.txt"
        assert generate_output_filename("test", "gbk") == "test_gbk"
        assert generate_output_filename("test.txt", "utf-8-sig") == "test_utf-8-sig.txt"

    def test_generate_output_filename_no_ext(self):
        """测试无扩展名文件"""
        assert generate_output_filename("README", "utf-8") == "README_utf-8"

    def test_generate_output_filename_complex(self):
        """测试复杂文件名"""
        assert generate_output_filename("my.file.name.txt", "gbk") == "my.file.name_gbk.txt"
        assert generate_output_filename("中文文件名.csv", "utf-8") == "中文文件名_utf-8.csv"


class TestIsTextFile:
    """测试文本文件判断"""

    def test_is_text_file_utf8(self, tmp_path):
        """测试 UTF-8 文本文件"""
        test_file = tmp_path / "text.txt"
        test_file.write_bytes("这是文本内容".encode('utf-8'))
        assert is_text_file(str(test_file)) is True

    def test_is_text_file_gbk(self, tmp_path):
        """测试 GBK 文本文件"""
        test_file = tmp_path / "text_gbk.txt"
        test_file.write_bytes("这是文本内容".encode('gbk'))
        assert is_text_file(str(test_file)) is True

    def test_is_binary_file(self, tmp_path):
        """测试二进制文件"""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd\xfc')
        assert is_text_file(str(test_file)) is False


class TestGetFileInfo:
    """测试文件信息获取"""

    def test_get_file_info(self, tmp_path):
        """测试获取文件信息"""
        test_file = tmp_path / "info.txt"
        test_file.write_bytes(b'hello')
        info = get_file_info(str(test_file))
        assert info['name'] == 'info.txt'
        assert info['size'] == 5
        assert info['path'] == str(test_file)
