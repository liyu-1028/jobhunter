import os
import webbrowser
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from src.models import SearchResult, JobItem
from src.company_loader import CentralEnterpriseManager
from src.db import JobDatabase


class HTMLReportRenderer:
    """HTML 报告渲染与输出器 (将本地数据展示在统一的 output/index.html)"""

    def __init__(self, template_dir: str = "templates", output_dir: str = "output"):
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # 确保 output 目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.template = self.env.get_template("report_template.html")
        self.ent_manager = CentralEnterpriseManager()
        self.db = JobDatabase()

    def render(self, result: SearchResult, history_jobs: Optional[List[JobItem]] = None, open_browser: bool = True) -> str:
        """读取本地 SQLite 数据库，将抓取的数据写入 output/data.json 并更新渲染 output/index.html"""
        
        # 读取本地数据库全量历史数据
        history = history_jobs if history_jobs is not None else self.db.get_all_jobs()

        # 提取历史数据库中所有不同的搜索批次 / 日期
        batches = sorted(list(set([j.batch for j in history if j.batch])), reverse=True)

        # 获取全量央企名录与 2027 届校招章程数据
        enterprises = self.ent_manager.get_all_enterprises()

        # 1. 导出全量本地数据为独立的 output/data.json 文件
        json_path = os.path.abspath(os.path.join(self.output_dir, "data.json"))
        self.db.export_to_json(
            output_json_path=json_path,
            profile_dict=result.profile.model_dump() if result.profile else {},
            enterprises_list=enterprises
        )

        # 2. 渲染统一的本地静态 HTML 页面 output/index.html
        rendered_html = self.template.render(
            search_time=result.search_time,
            profile=result.profile,
            jobs=result.jobs,
            history_jobs=history,
            batches=batches,
            enterprises=enterprises,
            summary=result.summary
        )

        file_path = os.path.abspath(os.path.join(self.output_dir, "index.html"))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        print(f"\n✨ 本地可视化页面已展示最新数据: {file_path}")

        if open_browser:
            try:
                webbrowser.open(f"file://{file_path}")
                print("🌐 已在浏览器中打开本地 index.html 页面！")
            except Exception as e:
                print(f"⚠️ 无法自动打开浏览器，请手动用浏览器打开: {e}")

        return file_path
