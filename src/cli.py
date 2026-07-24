import os
import questionary
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from src.models import UserProfile
from src.engine import create_default_engine
from src.renderer import HTMLReportRenderer
from src.db import JobDatabase
from src.adapters.counselor_adapter import CounselorJobAdapter

console = Console()

def run_cli():
    console.print(Panel.fit("[bold blue]JobHunter 多源岗位匹配、央国企及高校辅导员抓取系统[/bold blue]", subtitle="DeepSeek AI & 统一时间戳数据库"))

    action = questionary.select(
        "请选择操作模式:",
        choices=[
            "1. 🚀 智能多数据源岗位搜索 (多维匹配)",
            "2. 🎓 抓取全国/特定省市高校辅导员岗位数据",
            "3. 📊 重新导出并生成可视化仪表盘 (output/index.html)",
            "4. ❌ 退出"
        ]
    ).ask()

    if action.startswith("4"):
        return

    db = JobDatabase()
    renderer = HTMLReportRenderer()
    # 建立本轮发起的统一时间戳 (同一批数据时间戳相同)
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action.startswith("1"):
        profile = UserProfile(
            degree="硕士", school="浙江大学", major="计算机",
            batch="2026届秋招", target_industry="互联网",
            company_type="大厂/国企", company_size="1000人以上",
            location="杭州", keywords="Python, 大模型"
        )
        engine = create_default_engine()
        result = engine.search_all_sources(profile)

        # 给该批次所有岗位赋予统一时间戳
        for job in result.jobs:
            job.fetched_at = batch_timestamp

        db.save_jobs(result.jobs, batch_timestamp=batch_timestamp)

        # 同时也抓取匹配城市的高校辅导员数据打上统一时间戳
        counselor_adapter = CounselorJobAdapter()
        counselor_jobs = counselor_adapter.fetch_counselor_jobs(province="浙江", city="杭州", batch_timestamp=batch_timestamp)
        db.save_counselor_jobs(counselor_jobs, batch_timestamp=batch_timestamp)

        all_history = db.get_all_jobs()
        report_file = renderer.render(result, history_jobs=all_history, open_browser=True)

    elif action.startswith("2"):
        prov = questionary.text("请输入查询省份 (例如: 浙江, 江苏, 北京, 广东, 四川, 或 all):", default="浙江").ask()
        city = questionary.text("请输入查询城市 (例如: 杭州, 南京, 北京, 广州, 深圳, 成都, 或 all):", default="杭州").ask()

        console.print(f"🔎 正在抓取 [bold cyan]{prov} · {city}[/bold cyan] 高校辅导员招聘岗位信息...")
        counselor_adapter = CounselorJobAdapter()
        counselor_jobs = counselor_adapter.fetch_counselor_jobs(province=prov, city=city, batch_timestamp=batch_timestamp)
        
        saved_count = db.save_counselor_jobs(counselor_jobs, batch_timestamp=batch_timestamp)
        console.print(f"✅ 成功抓取并落库 [bold green]{saved_count}[/bold green] 条高校辅导员招聘岗位数据 (时间戳: {batch_timestamp})！")

        # 渲染更新 html
        engine = create_default_engine()
        profile = UserProfile()
        result = engine.search_all_sources(profile)
        all_history = db.get_all_jobs()
        renderer.render(result, history_jobs=all_history, open_browser=True)

    elif action.startswith("3"):
        engine = create_default_engine()
        profile = UserProfile()
        result = engine.search_all_sources(profile)
        all_history = db.get_all_jobs()
        renderer.render(result, history_jobs=all_history, open_browser=True)

if __name__ == "__main__":
    run_cli()
