"""
测试核心编码转换模块
"""

import os
import pytest

from converter.encoder import Encoder, convert_file, get_supported_encodings


class TestConvertFile:
    """测试 convert_file 函数"""

    def test_gbk_to_utf8(self, tmp_path):
        """测试 GBK 转 UTF-8"""
        src = tmp_path / "test_gbk.txt"
        dst = tmp_path / "test_utf8.txt"
        content = "中文测试内容123"
        src.write_bytes(content.encode('gbk'))

        result = convert_file(str(src), str(dst), 'gbk', 'utf-8')
        assert result is True
        assert dst.read_bytes().decode('utf-8') == content

    def test_utf8_to_gbk(self, tmp_path):
        """测试 UTF-8 转 GBK"""
        src = tmp_path / "test_utf8.txt"
        dst = tmp_path / "test_gbk2.txt"
        content = "Hello 世界"
        src.write_bytes(content.encode('utf-8'))

        result = convert_file(str(src), str(dst), 'utf-8', 'gbk')
        assert result is True
        assert dst.read_bytes().decode('gbk') == content

    def test_empty_file(self, tmp_path):
        """测试空文件转换"""
        src = tmp_path / "empty.txt"
        dst = tmp_path / "empty_out.txt"
        src.write_bytes(b'')

        result = convert_file(str(src), str(dst), 'utf-8', 'utf-8')
        assert result is True
        assert dst.read_bytes() == b''

    def test_unicode_content(self, tmp_path):
        """测试包含中/日/韩/emoji 的内容"""
        src = tmp_path / "unicode.txt"
        dst = tmp_path / "unicode_out.txt"
        content = "中文日本語한국어🎉🚀"
        src.write_bytes(content.encode('utf-8'))

        result = convert_file(str(src), str(dst), 'utf-8', 'utf-8')
        assert result is True
        assert dst.read_bytes().decode('utf-8') == content

    def test_invalid_encoding(self, tmp_path):
        """测试无效编码抛出异常"""
        src = tmp_path / "invalid.txt"
        dst = tmp_path / "invalid_out.txt"
        # 写入无法用 GBK 解码的字节序列
        src.write_bytes(b'\xff\xfe\x00\x01\x02')

        with pytest.raises(Exception):
            convert_file(str(src), str(dst), 'gbk', 'utf-8')

    def test_emoji_to_gbk_with_replace(self, tmp_path):
        """测试 emoji 转 GBK 时使用 replace 策略"""
        src = tmp_path / "emoji.txt"
        dst = tmp_path / "emoji_gbk.txt"
        content = "测试内容✅ 带emoji🎉"
        src.write_bytes(content.encode('utf-8'))

        # 使用 replace 策略，不应该抛出异常
        from converter.encoder import Encoder
        encoder = Encoder('utf-8', 'gbk', errors='replace')
        result = encoder.convert(str(src), str(dst))
        assert result is True

        # 读取转换后文件，应该包含 ? 替代无法编码的字符
        with open(str(dst), 'r', encoding='gbk') as f:
            converted = f.read()
        assert '?' in converted
        # 中文部分应该保留
        assert '测试内容' in converted

    def test_emoji_to_gbk_with_ignore(self, tmp_path):
        """测试 emoji 转 GBK 时使用 ignore 策略"""
        src = tmp_path / "emoji2.txt"
        dst = tmp_path / "emoji2_gbk.txt"
        content = "测试内容✅ 带emoji🎉"
        src.write_bytes(content.encode('utf-8'))

        from converter.encoder import Encoder
        encoder = Encoder('utf-8', 'gbk', errors='ignore')
        result = encoder.convert(str(src), str(dst))
        assert result is True

        with open(str(dst), 'r', encoding='gbk') as f:
            converted = f.read()
        assert '测试内容' in converted
        assert '✅' not in converted
        assert '🎉' not in converted


class TestEncoder:
    """测试 Encoder 类"""

    def test_get_supported_encodings(self):
        """测试支持的编码列表"""
        encodings = get_supported_encodings()
        assert isinstance(encodings, list)
        assert len(encodings) > 0
        assert ('UTF-8', 'utf-8') in encodings
        assert ('GBK', 'gbk') in encodings
        assert ('GB2312', 'gb2312') in encodings
        assert ('BIG5', 'big5') in encodings

    def test_encoder_convert(self, tmp_path):
        """测试 Encoder 类的 convert 方法"""
        src = tmp_path / "encoder_test.txt"
        dst = tmp_path / "encoder_out.txt"
        content = "Encoder 测试"
        src.write_bytes(content.encode('gbk'))

        encoder = Encoder('gbk', 'utf-8')
        result = encoder.convert(str(src), str(dst))
        assert result is True
        assert dst.read_bytes().decode('utf-8') == content
