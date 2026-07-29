import os
import sys

# 动态将项目根目录加入 sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import questionary
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from src.models import UserProfile
from src.engine import create_default_engine
from src.renderer import HTMLReportRenderer
from src.db import JobDatabase
from src.adapters.counselor_adapter import CounselorJobAdapter

# 装载本地 .env 配置 (DeepSeek / Serper / Tavily Key)
from dotenv import load_dotenv
load_dotenv()

console = Console()

def run_cli():
    console.print(Panel.fit("[bold blue]JobHunter 多源岗位匹配、央国企及高校辅导员公告抓取系统[/bold blue]", subtitle="DeepSeek AI & REST API 后端服务"))

    action = questionary.select(
        "请选择操作模式:",
        choices=[
            "1. 🌐 启动网页 HTTP REST API 服务 (在浏览器直接 Fetch 交互)",
            "2. 🚀 智能多数据源岗位搜索 (命令行抓取)",
            "3. 🎓 按省份与城市查询高校辅导员招聘公告与链接",
            "4. 📊 重新导出并生成可视化仪表盘 (output/index.html)",
            "5. ❌ 退出"
        ]
    ).ask()

    if action.startswith("5"):
        return

    db = JobDatabase()
    renderer = HTMLReportRenderer()
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action.startswith("1"):
        console.print("🚀 正在启动 JobHunter Web REST API 服务器 (访问端口: http://127.0.0.1:8000)...")
        import uvicorn
        uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=True)

    elif action.startswith("2"):
        profile = UserProfile(
            degree="硕士", school="浙江大学", major="计算机",
            batch="2026届秋招", target_industry="互联网",
            company_type="大厂/国企", company_size="1000人以上",
            location="杭州", keywords="Python, 大模型"
        )
        engine = create_default_engine()
        result = engine.search_all_sources(profile)

        for job in result.jobs:
            job.fetched_at = batch_timestamp

        db.save_jobs(result.jobs, batch_timestamp=batch_timestamp)

        counselor_adapter = CounselorJobAdapter()
        counselor_anns = counselor_adapter.fetch_university_counselor_announcements(province="浙江", city="杭州", batch_timestamp=batch_timestamp)
        db.save_counselor_announcements(counselor_anns, batch_timestamp=batch_timestamp)

        all_history = db.get_all_jobs()
        renderer.render(result, history_jobs=all_history, open_browser=True)

    elif action.startswith("3"):
        prov = questionary.text("请输入查询省份 (例如: 浙江, 江苏, 北京, 广东, 四川, 湖北, 上海, 或 all):", default="浙江").ask()
        city = questionary.text("请输入查询城市 (例如: 杭州, 南京, 北京, 广州, 深圳, 成都, 武汉, 上海, 或 all):", default="杭州").ask()

        console.print(f"🔎 正在查询 [bold cyan]{prov} · {city}[/bold cyan] 高效的辅导员招聘公告与状态...")
        counselor_adapter = CounselorJobAdapter()
        counselor_anns = counselor_adapter.fetch_university_counselor_announcements(province=prov, city=city, batch_timestamp=batch_timestamp)
        
        saved_count = db.save_counselor_announcements(counselor_anns, batch_timestamp=batch_timestamp)
        console.print(f"✅ 成功查询并持久化落库 [bold green]{saved_count}[/bold green] 所高校辅导员招聘公告记录 (时间戳: {batch_timestamp})！")

        engine = create_default_engine()
        profile = UserProfile()
        result = engine.search_all_sources(profile)
        all_history = db.get_all_jobs()
        renderer.render(result, history_jobs=all_history, open_browser=True)

    elif action.startswith("4"):
        engine = create_default_engine()
        profile = UserProfile()
        result = engine.search_all_sources(profile)
        all_history = db.get_all_jobs()
        renderer.render(result, history_jobs=all_history, open_browser=True)

if __name__ == "__main__":
    run_cli()
