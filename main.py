"""
文件字符集转换工具 - 程序入口

启动 GUI 应用程序。
"""

import sys
import os

# 添加项目根目录到 sys.path（支持从任意目录运行）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    """
    程序入口函数

    启动 GUI 主窗口。
    """
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
