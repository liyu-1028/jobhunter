<div align="center">

# 🚀 JobHunter (岗位智能匹配与招考直通车)

**基于 DeepSeek 大模型 + 多源真实搜索引擎 + RESTful API 的高性能求职与招考智能助手**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Windows EXE Ready](https://img.shields.io/badge/Windows--EXE-Supported-orange.svg)](docs/windows_exe_guide.md)

</div>

---

## 🌟 核心亮点

- 🎯 **岗位多维智能匹配 (Tab 1)**：根据求职者的学历背景、毕业院校、专业、目标批次与意向城市，由 DeepSeek 大模型驱动进行精准岗位匹配与梯度推荐。
- 🔍 **多源真实搜索引擎，根除大模型幻觉**：岗位引擎已重构为多源适配器架构，聚合 **牛客网 (Nowcoder)**、**海投网 (Haitou)** 实时岗位抓取与 **Serper / Tavily** 搜索引擎全网真实检索（支持查询词智能扩展），所有结果均带真实来源链接，并经 MD5 指纹并发去重。
- 🏛️ **245 所央国企校招直通车 & 2027 章程 (Tab 2)**：完整涵盖 245 家央国企名录（含总部地区与行业分类），一键 Fetch 最新招考开启进度与选拔要求。
- 🎓 **全国 34 省市高校辅导员招聘直通车 (Tab 3)**：辅导员引擎采用多源适配器架构（**高校求职网 Gaoxiaojob**、**Bing 搜索**、**Curated 精选官网直连**），实时抓取全国各大地级市最新辅导员招聘公告与直达链接，杜绝编造假数据。
- 🛡️ **仪表盘交互增强**：三大 Fetch 按钮内置请求防抖机制，重复点击自动拦截并提示，避免并发请求冲突。
- 🔒 **个人 API Key 隐私安全保密**：网页端输入框支持自定义配置 DeepSeek API Key，密钥仅保存在用户本地浏览器 LocalStorage，绝不上交或泄露。
- 📦 **Windows `.EXE` 单文件免安装部署**：集成 PyInstaller 自动化打包与 GitHub Actions 云端自动 Release，支持 Windows 环境下双击直接唤起本地 Edge 或 Chrome 浏览器使用。

---

## 🏗️ 架构说明

```
JobHunter/
├── src/
│   ├── server.py            # FastAPI RESTful 交互后端 API 服务
│   ├── cli.py               # 命令行交互式 CLI 入口 (rich + questionary)
│   ├── app_launcher.py      # Windows .EXE 客户端统一启动器 (唤起 Edge/Chrome)
│   ├── engine.py            # 多源岗位聚合去重搜索引擎 (线程池并发抓取)
│   ├── company_loader.py    # 245 家央国企名录加载与管理
│   ├── deepseek_client.py   # DeepSeek 大模型集成客户端
│   ├── models.py            # Pydantic 数据模型 (UserProfile / JobItem 等)
│   ├── db.py                # SQLite 数据库与 JSON 导出组件
│   ├── renderer.py          # Jinja2 动态仪表盘渲染引擎
│   ├── registry/
│   │   └── university_registry.py   # 全国高校名录注册表
│   └── adapters/            # 多源适配器集群
│       ├── deepseek_adapter.py      # DeepSeek 大模型智能匹配
│       ├── job_search_adapter.py    # Serper/Tavily 真实搜索聚合适配器
│       ├── serper_source.py         # Serper 搜索数据源
│       ├── tavily_source.py         # Tavily 搜索数据源
│       ├── query_expander.py        # 搜索关键词智能扩展器
│       ├── nowcoder.py              # 牛客网 (Nowcoder) 岗位源
│       ├── haitou.py                # 海投网 (Haitou) 岗位源
│       ├── counselor_adapter.py     # 高校辅导员聚合查询入口
│       ├── counselor_aggregator.py  # 辅导员多源结果聚合器
│       ├── counselor_gaoxiaojob.py  # 高校求职网 (Gaoxiaojob) 数据源
│       ├── counselor_bing.py        # Bing 搜索数据源
│       └── counselor_curated.py     # Curated 精选官网直连数据源
├── templates/
│   └── report_template.html # 优雅现代风单页仪表盘 HTML 模板 (含 Fetch 防抖)
├── config/
│   └── profile.yaml         # 个人求职画像配置文件
├── data/
│   ├── company.xlsx         # 245 家央国企名录工作表
│   └── curated_announcements.json  # 精选高校辅导员公告数据
├── docs/
│   └── assets/              # 微信二维码与赞赏收款码资源图片目录
├── scripts/
│   ├── start.sh / stop.sh   # 一键启动 / 停止脚本
│   ├── manage.sh            # Linux/macOS 后台守护脚本 (start/stop/restart)
│   ├── build_windows_exe.bat# Windows 一键编译 .EXE 批处理脚本
│   ├── build_exe.py         # 跨平台构建脚本
│   └── import_moe_list.py   # 高校名录数据导入脚本
├── tests/                   # 单元测试目录
└── .github/workflows/
    └── build_exe.yml        # GitHub Actions 自动化 Windows EXE 云端构建与 Release 工作流
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
在 `.env` 中填写以下密钥（也可直接在打开的网页端输入框配置 DeepSeek Key，密钥仅保存在本地）：

| 密钥 | 用途 | 获取方式 |
| :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | 大模型岗位智能匹配与结果提取 | [platform.deepseek.com](https://platform.deepseek.com) |
| `SERPER_API_KEY` | 岗位/公告全网真实搜索数据源 | [serper.dev](https://serper.dev)（注册送 2500 次） |
| `TAVILY_API_KEY` | 岗位/公告全网真实搜索数据源 | [tavily.com](https://tavily.com)（免费 1000 次/月） |

### 3. 启动后台 API 服务与仪表盘

```bash
# 使用快捷脚本启动服务
./scripts/start.sh

# 或使用 Python 模块直接启动
python -m src.server
```
服务启动后，在浏览器访问 `http://127.0.0.1:8000` 即可进入可视化仪表盘。

> 💡 也可以使用命令行交互模式：`python -m src.cli`

---

## 🖥️ Windows 单文件 `.EXE` 发送给别人使用

本项目支持打包为独立的单文件 `JobHunter.exe`，别人收到后**无需安装 Python 或任何环境，双击即可直接唤起 Edge/Chrome 浏览器使用**：

1. **直接在 GitHub 下载编译好的 `.exe`**：
   前往 [GitHub Releases 页面](https://github.com/liyu-1028/jobhunter/releases) 直接点击下载 `JobHunter.exe`。
2. **在 Windows 本地自行构建**：
   双击运行 `scripts/build_windows_exe.bat` 即可在 `dist/` 目录下生成 `JobHunter.exe`。

推送形如 `v1.0.0` 的 tag 后，GitHub Actions 会自动云端构建并发布新版 `.exe` 到 Releases。

详细打包与分发指南请参阅 [docs/windows_exe_guide.md](docs/windows_exe_guide.md)。

---

## 📜 常用 REST API 接口

以下接口均同时支持 `GET` 与 `POST` 两种请求方式：

- `/api/search_jobs`：接收个人求职条件 Query，多源并发检索并返回大模型智能匹配岗位列表。
- `/api/fetch_enterprises`：实时获取并刷新全量 245 家央企校招状态。
- `/api/fetch_counselors`：根据 `province` 和 `city` 参数，经多源适配器抓取并由 LLM 提取最新高校辅导员招聘公告。
- `GET /api/history`：获取全量本地历史持久化数据。

---

## ❤️ 赞赏与支持 (Sponsor) & 💬 交流联系

如果本项目帮助到了您的求职、招考或开发工作，欢迎点个 **⭐ Star** 或给作者喝一杯咖啡 ☕！

<div align="center">

| 💬 微信交流与问题反馈 | ❤️ 微信赞赏与支持 |
| :---: | :---: |
| <img src="docs/assets/wechat.jpg" width="220" alt="个人微信二维码" /> | <img src="docs/assets/sponsor_wechat.jpg" width="220" alt="微信赞赏收款码" /> |
| 扫描二维码添加作者微信 | 扫描二维码给予作者赞赏支持 |

</div>

---

## 📄 开源许可

本项目遵循 [MIT License](LICENSE) 开源协议。
