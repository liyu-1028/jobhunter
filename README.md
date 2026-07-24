<div align="center">

# 🚀 JobHunter (岗位智能匹配与招考直通车)

**基于 DeepSeek 大模型 + RESTful API + 全网搜索抓取的高性能求职与招考智能助手**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Windows EXE Ready](https://img.shields.io/badge/Windows--EXE-Supported-orange.svg)](docs/windows_exe_guide.md)

</div>

---

## 🌟 核心亮点

- 🎯 **岗位多维智能匹配 (Tab 1)**：根据求职者的学历背景、毕业院校、专业、目标批次与意向城市，由 DeepSeek 大模型驱动进行精准岗位匹配与梯度推荐。
- 🏛️ **245 所央国企校招直通车 & 2027 章程 (Tab 2)**：完整涵盖 245 家央国企名录（含总部地区与行业分类），一键 Fetch 最新招考开启进度与选拔要求。
- 🎓 **全国 34 省市高校辅导员招聘直通车 (Tab 3)**：结合搜索引擎网页抓取与大模型（DeepSeek）常识推导，实时提取全国各大地级市（如安徽芜湖、浙江杭州等）最新高校辅导员招聘公告与直达链接。
- 💻 **优雅交互可视化仪表盘**：包含极简响应式 Web 界面与全局 Null 安全防护机制。
- 📦 **Windows `.EXE` 单文件免安装部署**：集成 PyInstaller 自动化打包，支持 Windows 环境下双击直接唤起本地 Edge 或 Chrome 浏览器使用。

---

## 🏗️ 架构说明

```
JobHunter/
├── src/
│   ├── app_launcher.py      # Windows .EXE 客户端统一启动器 (唤起 Edge/Chrome)
│   ├── server.py            # FastAPI RESTful 交互后端 API
│   ├── engine.py            # 多源招聘搜索引擎组装类
│   ├── deepseek_client.py   # DeepSeek 大模型集成客户端
│   ├── db.py                # SQLite 数据库与 JSON 导出组件
│   ├── renderer.py          # Jinja2 动态仪表盘渲染引擎
│   └── adapters/            # 适配器目录 (高校辅导员搜抓与 LLM 提取)
├── templates/
│   └── report_template.html  # 优雅现代风单页仪表盘 HTML 模板
├── scripts/
│   ├── manage.sh            # Linux/macOS 后台守护脚本 (start/stop/restart)
│   ├── build_windows_exe.bat# Windows 一键编译 .EXE 批处理脚本
│   └── build_exe.py         # 跨平台构建脚本
└── .github/workflows/
    └── build_exe.yml        # GitHub Actions 自动化 Windows EXE 云端构建工作流
```

---

## ⚡ 快速开始

### 1. 克隆项目与配置环境

```bash
git clone https://github.com/liyu-1028/jobhunter.git
cd jobhunter

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate   # Windows 用户请运行: .venv\Scripts\activate

# 安装项目依赖
pip install -r requirements.txt
```

### 2. 配置 API Key (可选)

复制 `.env.example` 并重命名为 `.env`：
```bash
cp .env.example .env
```
在 `.env` 中填写您的 DeepSeek API Key（未配置时系统将自动降级为 Demo 智能 Mock 模式）。

### 3. 启动后台 API 服务与仪表盘

```bash
# 使用快捷脚本启动服务
./scripts/start.sh

# 或使用 Python 模块直接启动
python -m src.server
```
服务启动后，在浏览器访问 `http://127.0.0.1:8000` 即可进入可视化仪表盘。

---

## 🖥️ Windows 单文件 `.EXE` 发送给别人使用

本项目支持打包为独立的单文件 `JobHunter.exe`，别人收到后**无需安装 Python 或任何环境，双击即可直接唤起 Edge/Chrome 浏览器使用**：

1. **直接在 GitHub 下载编译好的 `.exe`**：
   前往 [GitHub Actions Release 页面](https://github.com/liyu-1028/jobhunter/actions)，选择最新运行构建成功的 Workflow，在 Artifacts 中即可下载 `JobHunter.exe`。
2. **在 Windows 本地自行构建**：
   双击运行 `scripts/build_windows_exe.bat` 即可在 `dist/` 目录下生成 `JobHunter.exe`。

详细打包与分发指南请参阅 [docs/windows_exe_guide.md](docs/windows_exe_guide.md)。

---

## 📜 常用 REST API 接口

- `POST /api/search_jobs`：接收个人求职条件 Query，返回大模型智能匹配岗位列表。
- `POST /api/fetch_enterprises`：实时获取并刷新全量 245 家央企校招状态。
- `POST /api/fetch_counselors`：根据 `province` 和 `city` 参数抓取并经由 LLM 提取最新高校辅导员招聘公告。
- `GET /api/history`：获取全量本地历史持久化数据。

---

## 📄 开源许可

本项目遵循 [MIT License](LICENSE) 开源协议。
