import os
import sys

# 将项目根目录添加到 Python 模块搜索路径 sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from src.models import UserProfile
from src.engine import create_default_engine
from src.company_loader import CentralEnterpriseManager
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase
from src.renderer import HTMLReportRenderer

app = FastAPI(title="JobHunter RESTful API Server", description="多维度岗位匹配、央国企及高校辅导员 Fetch 服务")

db = JobDatabase()
engine = create_default_engine()
ent_manager = CentralEnterpriseManager()
counselor_adapter = CounselorJobAdapter()
renderer = HTMLReportRenderer()


class CounselorFetchRequest(BaseModel):
    province: str = "all"
    city: str = "all"


@app.get("/", response_class=HTMLResponse)
def index_page():
    """提供首页可视化仪表盘文件"""
    index_path = os.path.abspath("output/index.html")
    if not os.path.exists(index_path):
        profile = UserProfile()
        res = engine.search_all_sources(profile)
        renderer.render(res, history_jobs=db.get_all_jobs())
    return FileResponse(index_path)


@app.post("/api/search_jobs")
def api_search_jobs(profile: UserProfile):
    """【Tab 1】接收个人信息表单，实时并发抓取并匹配岗位"""
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    search_res = engine.search_all_sources(profile)

    for job in search_res.jobs:
        job.fetched_at = batch_timestamp

    db.save_jobs(search_res.jobs, batch_timestamp=batch_timestamp)
    all_history = db.get_all_jobs()

    renderer.render(search_res, history_jobs=all_history)

    return {
        "status": "success",
        "fetched_at": batch_timestamp,
        "total_jobs": len(all_history),
        "new_matched": len(search_res.jobs),
        "jobs": all_history
    }


@app.post("/api/fetch_enterprises")
def api_fetch_enterprises():
    """【Tab 2】刷新全量 245 家央国企招考状态与选拔章程"""
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    enterprises = ent_manager.get_all_enterprises()

    with db._get_connection() as conn:
        conn.execute("UPDATE central_enterprises SET updated_at = ?", (batch_timestamp,))
        conn.commit()

    db.export_to_json()
    enterprises = ent_manager.get_all_enterprises()

    return {
        "status": "success",
        "fetched_at": batch_timestamp,
        "total_enterprises": len(enterprises),
        "enterprises": enterprises
    }


@app.post("/api/fetch_counselors")
def api_fetch_counselors(req: CounselorFetchRequest):
    """【Tab 3】按省份和城市实时 Fetch 最新高校辅导员招聘公告与链接"""
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    anns = counselor_adapter.fetch_university_counselor_announcements(
        province=req.province,
        city=req.city,
        batch_timestamp=batch_timestamp
    )

    db.save_counselor_announcements(anns, batch_timestamp=batch_timestamp)
    all_anns = db.get_all_counselor_announcements()

    return {
        "status": "success",
        "fetched_at": batch_timestamp,
        "total_announcements": len(all_anns),
        "matched_count": len(anns),
        "counselors": all_anns
    }


@app.get("/api/history")
def api_get_history():
    """获取全量历史数据"""
    jobs = db.get_all_jobs()
    enterprises = ent_manager.get_all_enterprises()
    counselors = db.get_all_counselor_announcements()

    timestamps = list(set([j.get('fetched_at', '') for j in jobs if j.get('fetched_at')]))
    timestamps.extend(list(set([c.get('fetched_at', '') for c in counselors if c.get('fetched_at')])))
    timestamps = sorted(list(set(timestamps)), reverse=True)

    return {
        "jobs": jobs,
        "enterprises": enterprises,
        "counselors": counselors,
        "timestamps": timestamps
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 正在启动 JobHunter 本地 HTTP API 服务器 (访问端口: 8000)...")
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=True)
