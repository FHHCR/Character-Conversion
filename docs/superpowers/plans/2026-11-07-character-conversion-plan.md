# 文件字符集转换工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个 Windows 可视化文件字符集转换工具，支持批量转换常见编码（GBK、UTF-8、GB2312、BIG5 等）。

**Architecture:** Python + Tkinter 构建桌面应用。核心转换逻辑独立于 GUI（converter/ 模块），GUI 层调用核心模块。这种分层设计确保核心逻辑可独立测试，不依赖 GUI 环境。

**Tech Stack:** Python 3.10+, Tkinter（标准库）, pytest（测试）

**Spec:** `docs/superpowers/specs/2026-11-07-character-conversion-design.md`

## Global Constraints

- Python 3.10+ 必须可用
- Tkinter 是 Python 标准库的一部分，无需额外安装
- 零第三方运行时依赖（仅测试使用 pytest）
- 默认不覆盖原文件，转换结果保存到输出目录
- 所有异常必须被捕获，程序不崩溃
- 文件读写使用明确的编码参数，不使用系统默认编码

## Review Focus

1. **空文件处理**：空文件（0 字节）应能正常转换，不报错
2. **不支持编码的输入**：文件内容无法用指定编码解码时，应抛出明确的异常信息
3. **输出目录不存在**：转换时输出目录不存在，应自动创建
4. **特殊字符**：包含中文、日文、韩文、emoji 等特殊字符的文件应能正确转换
5. **目标目录与源目录相同**：转换后文件名冲突时，应有明确的处理策略

---

## Task 1: 核心转换模块（encoder.py + utils.py）

**Files:**
- Create: `converter/__init__.py`
- Create: `converter/encoder.py`
- Create: `converter/utils.py`
- Create: `tests/__init__.py`
- Create: `tests/test_encoder.py`
- Create: `tests/test_utils.py`

**Interfaces:**
- Consumes: 无（第一个任务）
- Produces:
  - `converter.encoder.Encoder` 类
  - `converter.encoder.convert_file(source_path, target_path, source_encoding, target_encoding) -> bool`
  - `converter.encoder.get_supported_encodings() -> list[tuple[str, str]]`
  - `converter.utils.detect_encoding(file_path) -> str`
  - `converter.utils.format_size(size_bytes) -> str`
  - `converter.utils.ensure_dir(path) -> None`

- [ ] **Step 1: 编写失败测试 - test_encoder.py**

创建 `tests/test_encoder.py`，测试编码转换核心逻辑：

```python
import os
import pytest
from converter.encoder import Encoder, convert_file, get_supported_encodings

class TestConvertFile:
    def test_gbk_to_utf8(self, tmp_path):
        """测试 GBK 转 UTF-8"""
        src = tmp_path / "test_gbk.txt"
        dst = tmp_path / "test_utf8.txt"
        # 写入 GBK 编码内容
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
        src.write_bytes(b'\xff\xfe\x00\x01\x02')  # 无效 GBK 字节序列
        
        with pytest.raises(Exception):
            convert_file(str(src), str(dst), 'gbk', 'utf-8')

class TestEncoder:
    def test_get_supported_encodings(self):
        """测试支持的编码列表"""
        encodings = get_supported_encodings()
        assert isinstance(encodings, list)
        assert len(encodings) > 0
        assert ('UTF-8', 'utf-8') in encodings
        assert ('GBK', 'gbk') in encodings
        assert ('GB2312', 'gb2312') in encodings
        assert ('BIG5', 'big5') in encodings
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_encoder.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'converter'"

- [ ] **Step 3: 实现 converter/encoder.py**

```python
"""
核心编码转换模块
"""

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
    """返回支持的编码列表 [(显示名, 编码标识), ...]"""
    return SUPPORTED_ENCODINGS


class Encoder:
    """核心编码转换类"""
    
    def __init__(self, source_encoding, target_encoding):
        self.source_encoding = source_encoding
        self.target_encoding = target_encoding
    
    def convert(self, input_path, output_path):
        """
        转换文件编码
        
        Args:
            input_path: 源文件路径
            output_path: 输出文件路径
        
        Returns:
            bool: 转换是否成功
        
        Raises:
            UnicodeDecodeError: 源文件无法用指定编码解码
            UnicodeEncodeError: 目标编码无法表示源文件内容
        """
        with open(input_path, 'r', encoding=self.source_encoding) as f:
            content = f.read()
        
        with open(output_path, 'w', encoding=self.target_encoding) as f:
            f.write(content)
        
        return True


def convert_file(source_path, target_path, source_encoding, target_encoding):
    """
    转换文件编码（函数式接口）
    
    Args:
        source_path: 源文件路径
        target_path: 目标文件路径
        source_encoding: 源编码
        target_encoding: 目标编码
    
    Returns:
        bool: 转换是否成功
    """
    encoder = Encoder(source_encoding, target_encoding)
    return encoder.convert(source_path, target_path)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_encoder.py -v`
Expected: PASS (6 tests passed)

- [ ] **Step 5: 编写失败测试 - test_utils.py**

创建 `tests/test_utils.py`，测试工具函数：

```python
import os
import pytest
from converter.utils import detect_encoding, format_size, ensure_dir

class TestUtils:
    def test_format_size_bytes(self):
        """测试文件大小格式化"""
        assert format_size(0) == '0 B'
        assert format_size(1024) == '1.00 KB'
        assert format_size(1024 * 1024) == '1.00 MB'
        assert format_size(1024 * 1024 * 1024) == '1.00 GB'
    
    def test_format_size_edge(self):
        """测试文件大小格式化边界"""
        assert format_size(512) == '512 B'
        assert format_size(1536) == '1.50 KB'
    
    def test_ensure_dir(self, tmp_path):
        """测试创建目录"""
        target = tmp_path / "new" / "nested" / "dir"
        ensure_dir(str(target))
        assert target.exists()
        assert target.is_dir()
    
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
```

- [ ] **Step 6: 运行测试确认失败**

Run: `pytest tests/test_utils.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'converter.utils'"

- [ ] **Step 7: 实现 converter/utils.py**

```python
"""
工具函数模块
"""

import os
import codecs


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
    with open(file_path, 'rb') as f:
        raw = f.read(4)
    
    # 检查 BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    if raw.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    if raw.startswith(b'\xfe\xff'):
        return 'utf-16-be'
    
    # 读取更多内容检测
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
```

- [ ] **Step 8: 运行测试确认通过**

Run: `pytest tests/test_utils.py -v`
Expected: PASS (5 tests passed)

- [ ] **Step 9: 提交**

```bash
git add converter/ tests/
git commit -m "feat: add core conversion module and utilities"
```

---

## Task 2: GUI 界面模块

**Files:**
- Create: `gui/__init__.py`
- Create: `gui/app.py`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes:
  - `converter.encoder.Encoder`, `convert_file`, `get_supported_encodings`
  - `converter.utils.detect_encoding`, `format_size`, `ensure_dir`
- Produces:
  - `gui.app.App` 类（Tkinter 主窗口）

- [ ] **Step 1: 编写 GUI 测试 - test_app.py**

创建 `tests/test_app.py`，测试 GUI 的核心逻辑（不依赖显示环境，测试数据逻辑部分）：

```python
import pytest
from gui.app import App
from gui.app import validate_output_path, generate_output_filename

class TestAppLogic:
    def test_validate_output_path_creates_dir(self, tmp_path):
        """测试输出路径验证"""
        target = tmp_path / "output" / "nested"
        result = validate_output_path(str(target))
        assert result is True
        assert target.exists()
    
    def test_generate_output_filename(self):
        """测试输出文件名生成"""
        assert generate_output_filename("test.txt", "utf-8") == "test_utf-8.txt"
        assert generate_output_filename("test", "gbk") == "test_gbk"
        assert generate_output_filename("test.txt", "utf-8-sig") == "test_utf-8-sig.txt"
    
    def test_generate_output_filename_no_ext(self):
        """测试无扩展名文件"""
        assert generate_output_filename("README", "utf-8") == "README_utf-8"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_app.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'gui'"

- [ ] **Step 3: 实现 gui/app.py**

```python
"""
GUI 主界面模块
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from converter.encoder import Encoder, convert_file, get_supported_encodings
from converter.utils import detect_encoding, format_size, ensure_dir


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


class App(tk.Tk):
    """主应用窗口"""
    
    def __init__(self):
        super().__init__()
        self.title("文件字符集转换工具")
        self.geometry("800x600")
        self.minsize(700, 500)
        
        self.files = []  # [(path, name, size, source_encoding), ...]
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 顶部工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(toolbar, text="添加文件...", command=self.add_files).pack(side='left', padx=2)
        ttk.Button(toolbar, text="添加文件夹...", command=self.add_folder).pack(side='left', padx=2)
        ttk.Button(toolbar, text="清空列表", command=self.clear_files).pack(side='left', padx=2)
        
        # 文件列表区域
        list_frame = ttk.LabelFrame(self, text="文件列表")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('name', 'size', 'encoding', 'status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        self.tree.heading('name', text='文件名')
        self.tree.heading('size', text='大小')
        self.tree.heading('encoding', text='源编码')
        self.tree.heading('status', text='状态')
        self.tree.column('name', width=300)
        self.tree.column('size', width=100)
        self.tree.column('encoding', width=100)
        self.tree.column('status', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 转换设置区域
        settings = ttk.LabelFrame(self, text="转换设置")
        settings.pack(fill='x', padx=10, pady=5)
        
        # 编码选择
        encodings = get_supported_encodings()
        encoding_names = [e[0] for e in encodings]
        encoding_map = dict(encodings)
        
        ttk.Label(settings, text="源编码:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.source_encoding_var = tk.StringVar()
        self.source_encoding_combo = ttk.Combobox(settings, textvariable=self.source_encoding_var, 
                                                   values=encoding_names, state='readonly', width=15)
        self.source_encoding_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.source_encoding_combo.set('UTF-8')
        
        ttk.Label(settings, text="目标编码:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.target_encoding_var = tk.StringVar()
        self.target_encoding_combo = ttk.Combobox(settings, textvariable=self.target_encoding_var,
                                                   values=encoding_names, state='readonly', width=15)
        self.target_encoding_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.target_encoding_combo.set('UTF-8')
        
        # 输出目录
        ttk.Label(settings, text="输出目录:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.output_dir_var = tk.StringVar()
        ttk.Entry(settings, textvariable=self.output_dir_var, width=40).grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='we')
        ttk.Button(settings, text="浏览...", command=self.select_output_dir).grid(row=1, column=3, padx=5, pady=5)
        
        # 选项
        self.auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings, text="自动检测源编码", variable=self.auto_detect_var).grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings, text="覆盖原文件", variable=self.overwrite_var).grid(row=2, column=2, padx=5, pady=5, sticky='w')
        
        # 操作按钮区域
        actions = ttk.Frame(self)
        actions.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(actions, text="开始转换", command=self.start_conversion).pack(side='left', padx=2)
        ttk.Button(actions, text="清除日志", command=self.clear_log).pack(side='left', padx=2)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.pack(fill='both', expand=False, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap='word', state='disabled')
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
        # 进度条
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill='x')
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(anchor='w')
    
    def add_files(self):
        """添加文件到列表"""
        filetypes = [
            ("文本文件", "*.txt *.csv *.log *.ini *.conf *.xml *.json *.html *.md"),
            ("所有文件", "*.*")
        ]
        paths = filedialog.askopenfilenames(title="选择文件", filetypes=filetypes)
        self._add_paths(paths)
    
    def add_folder(self):
        """添加文件夹中的所有文件"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if not folder:
            return
        for root, dirs, files in os.walk(folder):
            for f in files:
                self._add_paths([os.path.join(root, f)])
    
    def _add_paths(self, paths):
        """添加文件路径到列表"""
        for path in paths:
            if path in [f[0] for f in self.files]:
                continue  # 跳过重复文件
            try:
                size = os.path.getsize(path)
                encoding = '自动' if self.auto_detect_var.get() else self.source_encoding_var.get()
                self.files.append((path, os.path.basename(path), size, encoding))
                self.tree.insert('', 'end', values=(
                    os.path.basename(path), format_size(size), encoding, '待转换'
                ))
                self.log(f"添加文件: {path}")
            except Exception as e:
                self.log(f"添加文件失败 {path}: {str(e)}")
    
    def clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.tree.delete(*self.tree.get_children())
        self.log("已清空文件列表")
    
    def select_output_dir(self):
        """选择输出目录"""
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)
            self.log(f"输出目录: {path}")
    
    def start_conversion(self):
        """开始转换"""
        if not self.files:
            messagebox.showwarning("警告", "请先添加要转换的文件")
            return
        
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        if not validate_output_path(output_dir):
            messagebox.showerror("错误", "无法创建输出目录")
            return
        
        source_encoding_name = self.source_encoding_var.get()
        target_encoding_name = self.target_encoding_var.get()
        
        encodings = dict(get_supported_encodings())
        source_encoding = encodings[source_encoding_name]
        target_encoding = encodings[target_encoding_name]
        
        self.log(f"开始转换: {len(self.files)} 个文件 ({source_encoding_name} -> {target_encoding_name})")
        self.progress['maximum'] = len(self.files)
        self.progress['value'] = 0
        
        success_count = 0
        fail_count = 0
        
        for i, (path, name, size, _) in enumerate(self.files):
            try:
                # 自动检测源编码
                if self.auto_detect_var.get():
                    source_encoding = detect_encoding(path)
                
                # 确定输出路径
                if self.overwrite_var.get():
                    output_path = path
                else:
                    output_path = os.path.join(output_dir, generate_output_filename(name, target_encoding))
                
                # 转换
                convert_file(path, output_path, source_encoding, target_encoding)
                
                success_count += 1
                self.tree.item(self.tree.get_children()[i], values=(
                    name, format_size(size), source_encoding, '成功'
                ))
                self.log(f"[成功] {name} -> {os.path.basename(output_path)}")
            except Exception as e:
                fail_count += 1
                self.tree.item(self.tree.get_children()[i], values=(
                    name, format_size(size), source_encoding, '失败'
                ))
                self.log(f"[失败] {name}: {str(e)}")
            
            self.progress['value'] = i + 1
            self.update_idletasks()
        
        self.status_var.set(f"转换完成: 成功 {success_count}, 失败 {fail_count}")
        messagebox.showinfo("完成", f"转换完成!\n成功: {success_count} 个文件\n失败: {fail_count} 个文件")
    
    def clear_log(self):
        """清除日志"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_app.py -v`
Expected: PASS (3 tests passed)

- [ ] **Step 5: 提交**

```bash
git add gui/ tests/test_app.py
git commit -m "feat: add GUI interface module"
```

---

## Task 3: 程序入口 + 打包配置 + README + LICENSE

**Files:**
- Create: `main.py`
- Create: `README.md`
- Create: `LICENSE`
- Create: `requirements-dev.txt`
- Create: `pyproject.toml` 或 `setup.cfg`（用于 PyInstaller 打包配置）

**Interfaces:**
- Consumes:
  - `gui.app.App`
- Produces:
  - 可运行程序入口 `main.py`

- [ ] **Step 1: 编写入口测试**

```python
# tests/test_main.py
import os
import sys

def test_main_importable():
    """测试 main 模块可导入"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import main
    assert hasattr(main, 'main')
    assert callable(main.main)
```

- [ ] **Step 2: 实现 main.py**

```python
"""
程序入口
"""

import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    """程序入口函数"""
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: 编写 README.md**

```markdown
# 文件字符集转换工具

一个 Windows 可视化文件字符集转换工具，支持批量转换常见编码。

## 功能特性

- 支持多文件/文件夹选择
- 支持常见编码转换（GBK、UTF-8、GB2312、BIG5 等）
- 自动检测文件编码
- 批量转换，显示进度
- 不覆盖原文件，安全可靠
- 结果日志记录

## 技术栈

- Python 3.10+
- Tkinter（GUI）
- pytest（测试）

## 安装与部署

### 环境要求

- Python 3.10 或更高版本

### 运行源码

```bash
# 克隆项目
git clone <repo-url>
cd Character-Conversion

# 运行
python main.py
```

### 打包为 exe（可选）

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --windowed --name=字符转换工具 main.py
```

## 使用方法

1. 启动程序
2. 点击"添加文件..."或"添加文件夹..."选择要转换的文件
3. 选择源编码和目标编码
4. 选择输出目录
5. 点击"开始转换"
6. 查看日志和进度

## 支持的编码

| 编码 | 说明 |
|------|------|
| UTF-8 | 标准 UTF-8 |
| UTF-8 BOM | 带 BOM 的 UTF-8 |
| UTF-16 LE | UTF-16 小端 |
| UTF-16 BE | UTF-16 大端 |
| GBK | 简体中文 |
| GB2312 | 简体中文（旧） |
| GB18030 | 简体中文（新） |
| BIG5 | 繁体中文 |
| Shift-JIS | 日文 |
| EUC-KR | 韩文 |
| ASCII | ASCII |
| Latin-1 | Latin-1 |

## 测试

```bash
# 安装依赖
pip install pytest

# 运行测试
pytest tests/ -v
```

## 许可证

MIT License

## 联系方式

- 作者：[作者名]
- 邮箱：[邮箱]
```

- [ ] **Step 4: 编写 LICENSE**

```markdown
MIT License

Copyright (c) 2026 [作者名]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 5: 编写 requirements-dev.txt**

```txt
pytest>=7.0.0
pyinstaller>=6.0.0
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/ -v`
Expected: PASS (全部测试通过)

- [ ] **Step 7: 提交**

```bash
git add main.py README.md LICENSE requirements-dev.txt
git commit -m "feat: add entry point, README, LICENSE and build config"
```

---

## 任务4: 打包配置（可选）

**Files:**
- Create: `CharacterConverter.spec`（PyInstaller 配置）

**Interfaces:**
- Consumes: `main.py`
- Produces: 可执行的 exe 文件

- [ ] **Step 1: 编写 PyInstaller 配置**

```python
# CharacterConverter.spec
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['converter', 'gui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='字符转换工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='字符转换工具',
)
```

- [ ] **Step 2: 验证配置可读**

Run: `python -c "import ast; ast.parse(open('CharacterConverter.spec').read()); print('Config OK')"`
Expected: Config OK

- [ ] **Step 3: 提交**

```bash
git add CharacterConverter.spec
git commit -m "chore: add PyInstaller build config"
```
