# JobHunter Windows .EXE 可执行文件获取与分发指南

本指南专为**将 JobHunter 打包为 Windows `.exe` 程序并直接发送给其他 Windows 用户使用**而设计。

别人收到 `JobHunter.exe` 后无需安装 Python 或任何环境，双击即可运行，系统会自动唤起其 Windows 本地的 **Microsoft Edge** 或 **Google Chrome** 浏览器访问界面。

---

### 🎁 方式 1: 直接获取官方云端为您编译好的 `JobHunter.exe` (最推荐)

项目已为您配置了 **GitHub Actions 云端自动构建系统**。每当提交代码时，云端 Windows 虚拟机就会自动为您编译生成标准的 `JobHunter.exe`：

1. 打开项目的 GitHub 仓库页面：[https://github.com/liyu-1028/jobhunter](https://github.com/liyu-1028/jobhunter)
2. 点击顶部 **`Actions`** 选项卡；
3. 选择最新运行成功的 **`Build Windows EXE Release`** 工作流；
4. 滚动到页面底部 **`Artifacts`** 区域，直接点击下载 **`JobHunter_Windows_Executable`**；
5. 解压出来的就是原汁原味的 **`JobHunter.exe`**！您可以直接通过微信、QQ、百度网盘或邮件发给任何人！

---

### 🛠️ 方式 2: 在任意 Windows 电脑上一键本地生成 `.exe`

如果您或您的朋友手头有一台 Windows 电脑，只需：
1. 将本项目压缩包发到 Windows 电脑上并解压；
2. 打开 `scripts\` 文件夹，双击运行 **`build_windows_exe.bat`** 脚本；
3. 稍等数秒，脚本会自动在桌面的 `dist\` 目录下生成：
   `JobHunter.exe`
4. 这个 `JobHunter.exe` 就是独立的绿色单文件，直接发送给其他人即可！

---

### 💡 别人收到 `JobHunter.exe` 后如何使用？

1. 别人直接**双击运行 `JobHunter.exe`**；
2. 程序会在后台静默启动服务，并在 1-2 秒内**自动唤起其 Windows 本地的 Edge 或 Chrome 浏览器**，打开：
   `http://127.0.0.1:8000`
3. 界面完全动态交互，支持搜索岗位、抓取 245 家央国企以及百度 LLM 检索全国高校辅导员公告！
