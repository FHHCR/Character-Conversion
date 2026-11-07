"""
GUI 主界面模块

提供 Tkinter 图形界面，实现文件字符集转换工具的完整交互。
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from converter.encoder import get_supported_encodings, convert_file
from converter.utils import detect_encoding, format_size, ensure_dir
from gui.core import validate_output_path, generate_output_filename


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
        # ========== 顶部工具栏 ==========
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=5)

        ttk.Button(toolbar, text="添加文件...", command=self.add_files).pack(side='left', padx=2)
        ttk.Button(toolbar, text="添加文件夹...", command=self.add_folder).pack(side='left', padx=2)
        ttk.Button(toolbar, text="清空列表", command=self.clear_files).pack(side='left', padx=2)

        # ========== 文件列表区域 ==========
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

        # ========== 转换设置区域 ==========
        settings = ttk.LabelFrame(self, text="转换设置")
        settings.pack(fill='x', padx=10, pady=5)

        # 编码选择
        encodings = get_supported_encodings()
        encoding_names = [e[0] for e in encodings]

        ttk.Label(settings, text="源编码:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.source_encoding_var = tk.StringVar()
        self.source_encoding_combo = ttk.Combobox(
            settings, textvariable=self.source_encoding_var,
            values=encoding_names, state='readonly', width=15
        )
        self.source_encoding_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.source_encoding_combo.set('UTF-8')

        ttk.Label(settings, text="目标编码:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.target_encoding_var = tk.StringVar()
        self.target_encoding_combo = ttk.Combobox(
            settings, textvariable=self.target_encoding_var,
            values=encoding_names, state='readonly', width=15
        )
        self.target_encoding_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.target_encoding_combo.set('UTF-8')

        # 输出目录
        ttk.Label(settings, text="输出目录:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.output_dir_var = tk.StringVar()
        ttk.Entry(settings, textvariable=self.output_dir_var, width=40).grid(
            row=1, column=1, columnspan=2, padx=5, pady=5, sticky='we'
        )
        ttk.Button(settings, text="浏览...", command=self.select_output_dir).grid(
            row=1, column=3, padx=5, pady=5
        )

        # 选项
        self.auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings, text="自动检测源编码", variable=self.auto_detect_var).grid(
            row=2, column=1, padx=5, pady=5, sticky='w'
        )

        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings, text="覆盖原文件", variable=self.overwrite_var).grid(
            row=2, column=2, padx=5, pady=5, sticky='w'
        )

        # 错误处理策略
        ttk.Label(settings, text="错误处理:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.errors_var = tk.StringVar()
        errors_options = [
            ('严格模式（报错）', 'strict'),
            ('替换字符（?）', 'replace'),
            ('忽略字符', 'ignore'),
            ('XML实体引用', 'xmlcharrefreplace'),
        ]
        self.errors_combo = ttk.Combobox(
            settings, textvariable=self.errors_var,
            values=[e[0] for e in errors_options], state='readonly', width=15
        )
        self.errors_combo.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.errors_combo.set('严格模式（报错）')
        self.errors_map = dict(errors_options)

        # ========== 操作按钮区域 ==========
        actions = ttk.Frame(self)
        actions.pack(fill='x', padx=10, pady=5)

        ttk.Button(actions, text="开始转换", command=self.start_conversion).pack(side='left', padx=2)
        ttk.Button(actions, text="清除日志", command=self.clear_log).pack(side='left', padx=2)

        # ========== 日志区域 ==========
        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.pack(fill='both', expand=False, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=8, wrap='word', state='disabled')
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')

        # ========== 进度条 ==========
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
        """
        添加文件路径到列表

        Args:
            paths: 文件路径列表
        """
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
        errors_option = self.errors_combo.get()
        errors_strategy = self.errors_map.get(errors_option, 'strict')

        encodings = dict(get_supported_encodings())
        source_encoding = encodings[source_encoding_name]
        target_encoding = encodings[target_encoding_name]

        self.log(f"开始转换: {len(self.files)} 个文件 ({source_encoding_name} -> {target_encoding_name}, 错误处理: {errors_option})")
        self.progress['maximum'] = len(self.files)
        self.progress['value'] = 0

        success_count = 0
        fail_count = 0

        # 获取所有树项目的 ID（保持顺序一致）
        tree_items = self.tree.get_children()

        for i, (path, name, size, _) in enumerate(self.files):
            try:
                # 自动检测源编码
                if self.auto_detect_var.get():
                    source_encoding = detect_encoding(path)

                # 确定输出路径
                if self.overwrite_var.get():
                    output_path = path
                else:
                    output_path = os.path.join(
                        output_dir,
                        generate_output_filename(name, target_encoding)
                    )

                # 执行转换（传递错误处理策略）
                convert_file(path, output_path, source_encoding, target_encoding, errors_strategy)

                success_count += 1
                # 更新树项目状态
                if i < len(tree_items):
                    self.tree.item(tree_items[i], values=(
                        name, format_size(size), source_encoding, '成功'
                    ))
                self.log(f"[成功] {name} -> {os.path.basename(output_path)}")
            except Exception as e:
                fail_count += 1
                # 更新树项目状态
                if i < len(tree_items):
                    self.tree.item(tree_items[i], values=(
                        name, format_size(size), source_encoding, '失败'
                    ))
                self.log(f"[失败] {name}: {str(e)}")

            self.progress['value'] = i + 1
            self.update_idletasks()

        self.status_var.set(f"转换完成: 成功 {success_count}, 失败 {fail_count}")
        messagebox.showinfo(
            "完成",
            f"转换完成!\n成功: {success_count} 个文件\n失败: {fail_count} 个文件"
        )

    def clear_log(self):
        """清除日志"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

    def log(self, message):
        """
        添加日志

        Args:
            message: 日志消息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
