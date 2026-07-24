#!/usr/bin/env python3
"""
JobHunter 一键自动化打包构建 Python 脚本
使用 PyInstaller 将项目打包为独立的单文件可执行程序 (Windows .exe / macOS 可执行程序)
"""
import os
import sys
import subprocess

def run_build():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    print("=" * 60)
    print("      🚀 JobHunter 自动化构建打包程序      ")
    print("=" * 60)

    # 1. 确保安装 PyInstaller
    print("\n📦 正在检查与安装打包依赖 PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    spec_file = os.path.join(project_root, "jobhunter.spec")
    if not os.path.exists(spec_file):
        print(f"❌ 找不到打包规格文件: {spec_file}")
        sys.exit(1)

    # 2. 执行 PyInstaller 打包
    print(f"\n⚙️ 正在使用 PyInstaller 编译打包 [{spec_file}]...")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_dir = os.path.join(project_root, "dist")
        print("\n" + "=" * 60)
        print("  ✅ 构建打包成功！")
        print(f"  📍 输出目录: {dist_dir}")
        print("  💡 Windows 下生成文件为: dist/JobHunter.exe")
        print("=" * 60)
    else:
        print("\n❌ 打包过程出现错误，请检查日志！")

if __name__ == "__main__":
    run_build()
