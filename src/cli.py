import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from src.models import UserProfile
from src.engine import create_default_engine
from src.renderer import HTMLReportRenderer
from src.db import JobDatabase

console = Console()


def load_config_profile(config_path: str = "config/profile.yaml") -> UserProfile | None:
    """尝试读取 YAML 配置文件"""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "user_profile" in data:
                    return UserProfile(**data["user_profile"])
        except Exception as e:
            console.print(f"[yellow]⚠️ 读取配置文件失败 ({e})，将切换到交互输入模式。[/yellow]")
    return None


def save_config_profile(profile: UserProfile, config_path: str = "config/profile.yaml"):
    """保存 UserProfile 到 YAML"""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"user_profile": profile.model_dump()}, f, allow_unicode=True)
    console.print(f"[green]✔ 已将当前求职 Profile 保存到配置文件: {config_path}[/green]")


def collect_profile_interactively(default_profile: UserProfile | None = None) -> UserProfile:
    """在终端中交互式收集用户个人求职信息"""
    console.print("\n[bold cyan]📝 请输入您的个人求职信息与搜索偏好：[/bold cyan]\n")

    degree = Prompt.ask(
        "🎓 1. 学历", 
        choices=["本科", "硕士", "博士", "大专"], 
        default=default_profile.degree if default_profile else "硕士"
    )

    school = Prompt.ask(
        "🏫 2. 毕业学校名称", 
        default=default_profile.school if default_profile else "浙江大学"
    )

    major = Prompt.ask(
        "📚 3. 专业名称", 
        default=default_profile.major if default_profile else "计算机科学与技术"
    )

    batch = Prompt.ask(
        "📅 4. 招聘批次", 
        default=default_profile.batch if default_profile else "2026届秋招"
    )

    target_industry = Prompt.ask(
        "🏢 5. 目标行业/领域", 
        default=default_profile.target_industry if default_profile else "互联网/人工智能/软件"
    )

    company_type = Prompt.ask(
        "🏛️ 6. 期望公司性质", 
        default=default_profile.company_type if default_profile else "大厂/国企/外企"
    )

    company_size = Prompt.ask(
        "👥 7. 期望公司规模人数", 
        default=default_profile.company_size if default_profile else "1000人以上"
    )

    location = Prompt.ask(
        "📍 8. 期望工作城市", 
        default=default_profile.location if default_profile else "杭州/上海"
    )

    keywords = Prompt.ask(
        "🔍 9. 搜索岗位关键词 (用逗号或空格分隔)", 
        default=default_profile.keywords if default_profile else "Python后端工程师, 算法工程师, 大模型开发"
    )

    profile = UserProfile(
        degree=degree,
        school=school,
        major=major,
        batch=batch,
        target_industry=target_industry,
        company_type=company_type,
        company_size=company_size,
        location=location,
        keywords=keywords
    )

    if Confirm.ask("\n💾 是否将上述求职 Profile 保存到本地配置文件以备下次快速运行？"):
        save_config_profile(profile)

    return profile


def run_cli():
    """CLI 主流程入口"""
    load_dotenv()
    
    console.print(Panel.fit(
        "[bold magenta]🚀 JobHunter - 多数据源智能岗位搜索与可视化投递助手[/bold magenta]\n"
        "[dim]集成 DeepSeek AI + 牛客网 + 海投网多数据源聚合 | MD5 无感去重 | SQLite 持久化[/dim]",
        border_style="cyan"
    ))

    # 1. 尝试读取预存的 Profile
    existing_profile = load_config_profile()
    profile = None

    if existing_profile:
        table = Table(title="📋 已加载保存的求职 Profile", border_style="dim")
        table.add_column("配置项", style="cyan")
        table.add_column("设定值", style="white")

        table.add_row("学历 & 学校", f"{existing_profile.degree} · {existing_profile.school}")
        table.add_row("专业", existing_profile.major)
        table.add_row("招聘批次", existing_profile.batch)
        table.add_row("目标行业 & 期望性质", f"{existing_profile.target_industry} ({existing_profile.company_type})")
        table.add_row("公司规模 & 城市", f"{existing_profile.company_size} @ {existing_profile.location}")
        table.add_row("岗位关键词", existing_profile.keywords)

        console.print(table)

        use_existing = Confirm.ask("是否直接使用以上求职 Profile 开始搜索？", default=True)
        if use_existing:
            profile = existing_profile

    if not profile:
        profile = collect_profile_interactively(default_profile=existing_profile)

    # 2. 检查 DeepSeek API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        console.print("\n[bold yellow]⚠️ 未检测到环境变量 DEEPSEEK_API_KEY。[/bold yellow]")
        user_input_key = Prompt.ask("🔑 请输入您的 DeepSeek API Key (回车则跳过并使用 Demo 体验模式)", default="")
        if user_input_key.strip():
            api_key = user_input_key.strip()
            os.environ["DEEPSEEK_API_KEY"] = api_key

    # 3. 启动多数据源引擎并发检索
    engine = create_default_engine(api_key=api_key)

    with console.status("[bold green]🤖 多数据源引擎 (DeepSeek + 牛客网 + 海投网) 正在并发检索并去重，请稍候...", spinner="dots"):
        result = engine.search_all_sources(profile)

    # 4. 持久化数据落库 SQLite
    db = JobDatabase()
    db.save_jobs(result.jobs)
    all_history_jobs = db.get_all_jobs()

    console.print(f"\n[bold green]✅ 多源并发检索完成！聚合去重后共得出 {len(result.jobs)} 个精选岗位！(历史数据库累计共 {len(all_history_jobs)} 个岗位)[/bold green]")

    # 5. 渲染可视化 HTML 报告（写入统一 output/index.html）
    renderer = HTMLReportRenderer()
    report_file = renderer.render(result, history_jobs=all_history_jobs, open_browser=True)

    console.print("\n[bold cyan]🎉 任务完成！赶快去浏览器查看您的多维筛选投递仪表盘 (output/index.html) 吧！[/bold cyan]")
