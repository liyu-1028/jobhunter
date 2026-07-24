# JobHunter Windows .EXE 独立客户端构建与使用指南

JobHunter 已支持完整打包为单文件 `JobHunter.exe`。用户在 Windows 环境下双击运行后，将后台静默启动服务并**自动唤起本地默认浏览器（Edge / Chrome）**直接使用！

---

### 🚀 方案 1: 直接运行已打包的 `dist/JobHunter.exe`

如果您手中已有编译好的 `JobHunter.exe`：
1. **双击运行** `JobHunter.exe`；
2. 程序会自动寻找空闲端口，并在 1.5 秒内自动调用 Windows 系统本地的 **Microsoft Edge** 或 **Google Chrome** 浏览器，自动打开页面：
   `http://127.0.0.1:8000`
3. 提示：保留黑框控制台窗口后台运行；使用完毕后关闭控制台窗口即可推出服务。

---

### 🛠️ 方案 2: 在 Windows 环境下自行源码构建打包

如果您需要在 Windows 机器上根据最新源码重新生成 `.exe`：

#### 方法 A：使用一键批处理脚本 (推荐)
1. 将项目代码复制到 Windows 机器；
2. 进入 `scripts\` 目录，双击运行 **`build_windows_exe.bat`**；
3. 脚本会自动安装所需依赖并调用 `PyInstaller` 编译，生成目标程序：
   `dist\JobHunter.exe`

#### 方法 B：使用 Python 脚本构建
在 Windows 命令提示符 (CMD) 或 PowerShell 中运行：
```cmd
python scripts/build_exe.py
```

---

### 🌐 浏览器兼容与技术亮点

- **浏览器唤起机制**：利用 Python 标准 `webbrowser` 接口，自动对齐 Windows `http/https` 协议关联，优先唤起 Windows 10/11 内置的 **Microsoft Edge** 或 **Google Chrome**。
- **静态资源零丢失**：使用 `sys._MEIPASS` 兼容机制，保证打包为 `.exe` 后模板文件（`templates/report_template.html`）与渲染数据库 100% 完整封装在可执行程序内部。
- **极简跨平台**：不需要安装任何 Python 环境与第三方依赖，开箱即用。
