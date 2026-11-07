"""
核心编码转换模块

提供文件字符集编码转换功能，支持常见编码格式：
- UTF-8 / UTF-8 BOM
- UTF-16 LE / BE
- GBK / GB2312 / GB18030
- BIG5
- Shift-JIS / EUC-KR
- ASCII / Latin-1
"""

# 支持的编码列表: [(显示名, 编码标识), ...]
SUPPORTED_ENCODINGS = [
    ('UTF-8', 'utf-8'),
    ('UTF-8 BOM', 'utf-8-sig'),
    ('UTF-16 LE', 'utf-16-le'),
    ('UTF-16 BE', 'utf-16-be'),
    ('GBK', 'gbk'),
    ('GB2312', 'gb2312'),
    ('GB18030', 'gb18030'),
    ('BIG5', 'big5'),
    ('Shift-JIS', 'shift_jis'),
    ('EUC-KR', 'euc_kr'),
    ('ASCII', 'ascii'),
    ('Latin-1', 'latin-1'),
]


def get_supported_encodings():
    """
    返回支持的编码列表

    Returns:
        list[tuple[str, str]]: [(显示名, 编码标识), ...]
    """
    return SUPPORTED_ENCODINGS


class Encoder:
    """核心编码转换类"""

    def __init__(self, source_encoding, target_encoding, errors='strict'):
        """
        初始化编码转换器

        Args:
            source_encoding: 源编码（如 'gbk', 'utf-8'）
            target_encoding: 目标编码（如 'utf-8', 'gbk'）
            errors: 错误处理策略，可选值：
                - 'strict': 严格模式，无法编码时抛出异常（默认）
                - 'replace': 用 '?' 替换无法编码的字符
                - 'ignore': 忽略无法编码的字符
                - 'xmlcharrefreplace': 用 XML 实体引用替换
        """
        self.source_encoding = source_encoding
        self.target_encoding = target_encoding
        self.errors = errors

    def convert(self, input_path, output_path):
        """
        转换文件编码

        Args:
            input_path: 源文件路径
            output_path: 目标文件路径

        Returns:
            bool: 转换是否成功

        Raises:
            UnicodeDecodeError: 源文件无法用指定编码解码
            UnicodeEncodeError: 目标编码无法表示源文件内容（errors='strict' 时）
            FileNotFoundError: 源文件不存在
        """
        # 读取源文件（使用源编码）
        with open(input_path, 'r', encoding=self.source_encoding) as f:
            content = f.read()

        # 写入目标文件（使用目标编码，支持错误处理策略）
        with open(output_path, 'w', encoding=self.target_encoding, errors=self.errors) as f:
            f.write(content)

        return True


def convert_file(source_path, target_path, source_encoding, target_encoding, errors='strict'):
    """
    转换文件编码（函数式接口）

    Args:
        source_path: 源文件路径
        target_path: 目标文件路径
        source_encoding: 源编码
        target_encoding: 目标编码
        errors: 错误处理策略（'strict'/'replace'/'ignore'/'xmlcharrefreplace'）

    Returns:
        bool: 转换是否成功

    Raises:
        UnicodeDecodeError: 源文件无法用指定编码解码
        UnicodeEncodeError: 目标编码无法表示源文件内容（errors='strict' 时）
    """
    encoder = Encoder(source_encoding, target_encoding, errors)
    return encoder.convert(source_path, target_path)
