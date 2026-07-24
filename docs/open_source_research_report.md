# JobHunter 开源准备与审计调研报告

## 1. 开源必要补充内容审计 (Open Source Compliance)
经检查，项目目前缺少以下开源必备文件：
- **LICENSE**：缺少开源协议文件（建议补充 MIT 或 Apache 2.0 协议）。
- **README.md**：项目根目录无说明文档，不利于其他开发者了解项目背景、功能特性、使用方法和部署流程。
- **CONTRIBUTING.md**：缺少代码贡献指南，无法规范外部贡献者的 PR 和 Issue 流程。
- **.env.example**：本地存在 `.env` 但缺少脱敏的模板文件，导致新用户不知道如何配置环境变量。

## 2. 个人隐私与敏感凭证泄露审计 (Privacy & Security Audit)
通过对全量代码和配置的审查，排查结果如下：
- **API Key 泄露风险**：
  - ⚠️ 项目根目录的 `.env` 文件中存在硬编码的真实 DeepSeek API Key（`sk-440b...`）。虽然 `.gitignore` 已包含 `.env`，但为彻底杜绝风险，强烈建议：
    1. 立即前往 DeepSeek 平台废除该旧 API Key 并重新生成。
    2. 检查 Git 历史，确认是否曾被意外提交。
- **个人隐私数据**：
  - 未在项目代码及配置文件中发现真实的个人姓名、邮箱、手机号等高敏信息。
  - 未发现 `C:\` 或 `/Users/liyanlong/...` 等开发环境绝对路径泄露。
  - `config/profile.yaml` 中含有部分教育背景信息（如“安徽师范大学”、“电子信息专业”），因不含强身份绑定信息，可视作 Demo 示例保留。

## 3. 远程仓库已被推送的非必要/冗余文件审计 (Remote Repo Files Clean-up)
检查发现项目内存在以下冗余或非必要文件。由于它们尚未被 `.gitignore` 规则完全覆盖，可能已被推送至 `origin/main` 远程仓库中：
- **运行生成产物**：`output/data.json`、`output/index.html`
- **进程状态文件**：`data/server.pid`
- **系统隐藏文件**：`.DS_Store`（根目录及子目录存在的系统文件）

### 清除指令与修复建议
如果上述文件已存在于远程仓库，请在项目根目录运行以下 Git 清除指令（该指令仅将文件移出版本控制，不会删除本地文件）：

```bash
# 1. 移除 MacOS 系统冗余文件
find . -name ".DS_Store" -exec git rm -r --cached {} \;

# 2. 移除生成的输出产物
git rm -r --cached output/data.json output/index.html

# 3. 移除进程状态文件
git rm -r --cached data/server.pid

# 4. 提交清理操作并推送到远程
git commit -m "chore: remove redundant files and artifacts from git tracking"
git push origin main
```

**后续修复建议**：请在 `.gitignore` 文件的末尾补充以下忽略规则，防止同类文件再次被意外推送：
```text
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes

# Output & Temp files
output/
data/*.pid
```
