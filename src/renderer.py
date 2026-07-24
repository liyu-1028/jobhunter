import os
import webbrowser
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from src.models import SearchResult


class HTMLReportRenderer:
    """HTML 报告渲染与输出器"""

    def __init__(self, template_dir: str = "templates", output_dir: str = "output"):
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # 确保 output 目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.template = self.env.get_template("report_template.html")

    def render(self, result: SearchResult, open_browser: bool = True) -> str:
        """渲染 HTML 报告并写入文件，返回生成的文件绝对路径"""
        rendered_html = self.template.render(
            search_time=result.search_time,
            profile=result.profile,
            jobs=result.jobs,
            summary=result.summary
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobs_{timestamp}.html"
        file_path = os.path.abspath(os.path.join(self.output_dir, filename))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        print(f"\n✨ 可视化 HTML 报告已成功生成: {file_path}")

        if open_browser:
            try:
                webbrowser.open(f"file://{file_path}")
                print("🌐 已在默认浏览器中打开岗位投递仪表盘！")
            except Exception as e:
                print(f"⚠️ 无法自动打开浏览器，请手动用浏览器打开上方路径: {e}")

        return file_path
