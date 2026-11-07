"""
测试程序入口模块（不依赖 tkinter）
"""

import os
import sys
import ast


def test_main_syntax():
    """测试 main.py 语法正确"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_path = os.path.join(project_root, 'main.py')
    with open(main_path, 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    assert True


def test_main_function_exists():
    """测试 main.py 包含 main 函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_path = os.path.join(project_root, 'main.py')
    with open(main_path, 'r', encoding='utf-8') as f:
        source = f.read()
    assert 'def main():' in source
    assert 'if __name__ ==' in source


def test_gui_app_syntax():
    """测试 gui/app.py 语法正确"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, 'gui', 'app.py')
    with open(app_path, 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    assert True


def test_gui_core_importable():
    """测试 gui/core.py 可导入"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    from gui.core import validate_output_path, generate_output_filename
    assert callable(validate_output_path)
    assert callable(generate_output_filename)


def test_project_structure():
    """测试项目结构完整"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_files = [
        'main.py',
        'README.md',
        'LICENSE',
        'converter/encoder.py',
        'converter/utils.py',
        'gui/app.py',
        'gui/core.py',
        'requirements-dev.txt'
    ]
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        assert os.path.exists(full_path), f"缺少文件: {file_path}"
