import os
import sys
import webbrowser
from jinja2 import Environment, FileSystemLoader
from src.models import SearchResult
from src.company_loader import CentralEnterpriseManager
from src.db import JobDatabase

class HTMLReportRenderer:
    """HTML 单页多维交互可视化仪表盘渲染类"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # 兼容 PyInstaller EXE 解压后的临时资源目录 sys._MEIPASS
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            template_dir = os.path.join(base_path, "templates")

        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.ent_manager = CentralEnterpriseManager()
        self.db = JobDatabase()

    def render(self, result: SearchResult, history_jobs: list = None, output_file: str = None, open_browser: bool = False) -> str:
        if output_file is None:
            if getattr(sys, 'frozen', False):
                # 打包运行环境下将生成的 output/index.html 放在用户工作目录或系统临时输出目录
                base_out = os.getcwd()
            else:
                base_out = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            output_file = os.path.join(base_out, "output", "index.html")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        template = self.env.get_template("report_template.html")

        if history_jobs is None:
            history_jobs = [j.dict() for j in result.jobs]

        # 获取全量央企名录与高校辅导员招聘公告
        enterprises = self.ent_manager.get_all_enterprises()
        counselor_anns = self.db.get_all_counselor_announcements()

        # 收集批次与时间戳
        batches = list(set([j.get('batch', '') for j in history_jobs if j.get('batch')]))
        timestamps = list(set([j.get('fetched_at', '') for j in history_jobs if j.get('fetched_at')]))

        html_content = template.render(
            profile=result.dict().get('profile', {}),
            search_time=result.search_time,
            total_found=len(history_jobs),
            jobs=result.jobs,
            history_jobs=history_jobs,
            enterprises=enterprises,
            counselor_announcements=counselor_anns,
            batches=batches,
            timestamps=timestamps
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"\n✨ 本地可视化页面已展示最新数据: {os.path.abspath(output_file)}")

        if open_browser:
            webbrowser.open(f"file://{os.path.abspath(output_file)}")

        return os.path.abspath(output_file)
