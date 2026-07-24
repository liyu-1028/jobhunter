import os
import webbrowser
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from src.models import SearchResult, JobItem


class HTMLReportRenderer:
    """HTML 报告渲染与输出器 (统一生成到单一的 index.html)"""

    def __init__(self, template_dir: str = "templates", output_dir: str = "output"):
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # 确保 output 目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.template = self.env.get_template("report_template.html")

    def render(self, result: SearchResult, history_jobs: Optional[List[JobItem]] = None, open_browser: bool = True) -> str:
        """渲染 HTML 报告并覆写统一的 output/index.html"""
        
        history = history_jobs if history_jobs is not None else result.jobs

        # 提取历史数据库中所有不同的搜索批次 / 日期
        batches = sorted(list(set([j.batch for j in history if j.batch])), reverse=True)

        rendered_html = self.template.render(
            search_time=result.search_time,
            profile=result.profile,
            jobs=result.jobs,
            history_jobs=history,
            batches=batches,
            summary=result.summary
        )

        # 固定写入单一页面路径 output/index.html
        file_path = os.path.abspath(os.path.join(self.output_dir, "index.html"))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        print(f"\n✨ 可视化 HTML 统一仪表盘已更新: {file_path}")

        if open_browser:
            try:
                webbrowser.open(f"file://{file_path}")
                print("🌐 已在默认浏览器中打开/刷新仪表盘 (index.html)！")
            except Exception as e:
                print(f"⚠️ 无法自动打开浏览器，请手动用浏览器打开: {e}")

        return file_path
