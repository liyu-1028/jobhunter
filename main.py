#!/usr/bin/env python3
"""
JobHunter - 智能岗位搜索与可视化投递助手
统一入口文件
"""

import sys
from src.cli import run_cli

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\n👋 程序已由用户手动退出，祝您求职顺利！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 运行发生错误: {e}")
        sys.exit(1)
