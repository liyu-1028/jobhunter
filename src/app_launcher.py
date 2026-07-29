import os
import sys
import time
import socket
import threading
import webbrowser
import uvicorn

# 解决 PyInstaller 环境下静态资源与源码路径定位
if getattr(sys, 'frozen', False):
    # 如果是打包后的 EXE 运行环境
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将项目根目录放入 sys.path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

# 装载本地 .env 配置 (EXE 打包环境下无 .env 时自动跳过)
load_dotenv()

from src.server import app

def find_available_port(start_port: int = 8000) -> int:
    """寻找本地可用的 TCP 端口"""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(('127.0.0.1', port))
            if res != 0:
                return port
            port += 1
    return start_port

def open_browser(url: str):
    """延迟唤起 Windows 本地 Edge 或 Chrome 浏览器"""
    time.sleep(1.5)
    print(f"\n🌐 正在唤起系统默认浏览器 (Edge / Chrome) 访问: {url}")
    try:
        # webbrowser 会在 Windows 上优先调用系统默认注册的 Edge 或 Chrome
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器，请手动复制在浏览器中打开: {url} ({e})")

def main():
    print("=" * 65)
    print("      🚀 JobHunter 智能岗位与招考直通车客户端 (Windows EXE)      ")
    print("=" * 65)
    
    port = find_available_port(8000)
    server_url = f"http://127.0.0.1:{port}"
    
    print(f"📍 服务启动中...")
    print(f"🔗 本地 API 与可视化地址: {server_url}")
    print(f"💡 提示: 请勿关闭本黑框控制台窗口，关闭后服务将终止。")
    print("-" * 65)

    # 启动后台子线程唤起浏览器
    threading.Thread(target=open_browser, args=(server_url,), daemon=True).start()

    # 启动 Uvicorn HTTP Web 服务器
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")
    except KeyboardInterrupt:
        print("\n👋 JobHunter 服务已安全退出！")

if __name__ == "__main__":
    main()
