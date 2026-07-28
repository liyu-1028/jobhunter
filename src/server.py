import os
import sys

# 动态将项目根目录加入 sys.path
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = sys._MEIPASS
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from src.models import UserProfile
from src.engine import create_default_engine
from src.company_loader import CentralEnterpriseManager
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase
from src.renderer import HTMLReportRenderer

app = FastAPI(title="JobHunter RESTful API Server", description="多维度岗位匹配、央国企及高校辅导员 Fetch 服务")

# 全量开放 CORS 跨域限制
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = JobDatabase()
default_engine = create_default_engine()
ent_manager = CentralEnterpriseManager()
counselor_adapter = CounselorJobAdapter()
renderer = HTMLReportRenderer()


class CounselorFetchRequest(BaseModel):
    province: Optional[str] = "all"
    city: Optional[str] = "all"
    api_key: Optional[str] = None


class OptionalUserProfile(BaseModel):
    degree: Optional[str] = "硕士"
    school: Optional[str] = "浙江大学"
    major: Optional[str] = "计算机"
    batch: Optional[str] = "2026届秋招"
    target_industry: Optional[str] = "互联网"
    company_type: Optional[str] = "大厂/国企"
    company_size: Optional[str] = "1000人以上"
    location: Optional[str] = "杭州"
    keywords: Optional[str] = "Python, 大模型"
    api_key: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def index_page():
    """提供首页可视化仪表盘文件 (兼容 EXE 解压与运行时生成)"""
    if getattr(sys, 'frozen', False):
        base_out = os.getcwd()
    else:
        base_out = PROJECT_ROOT

    index_path = os.path.join(base_out, "output", "index.html")

    if not os.path.exists(index_path):
        profile = UserProfile()
        res = default_engine.search_all_sources(profile)
        renderer.render(res, history_jobs=db.get_all_jobs(), output_file=index_path)

    return FileResponse(index_path)


# --- API 1: /api/search_jobs (支持 GET & POST) ---
@app.api_route("/api/search_jobs", methods=["GET", "POST"])
def api_search_jobs(profile: Optional[OptionalUserProfile] = None):
    """【Tab 1】接收个人信息 Query，实时抓取并匹配岗位 (支持网页用户专属 API Key)"""
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if profile is None:
        profile = OptionalUserProfile()

    user_prof = UserProfile(
        degree=profile.degree or "硕士",
        school=profile.school or "浙江大学",
        major=profile.major or "计算机",
        batch=profile.batch or "2026届秋招",
        target_industry=profile.target_industry or "互联网",
        company_type=profile.company_type or "大厂/国企",
        company_size=profile.company_size or "1000人以上",
        location=profile.location or "杭州",
        keywords=profile.keywords or "Python",
        api_key=profile.api_key
    )

    # 若前端传来了用户专属 API Key，使用包含该 Key 的引擎，绝不消耗作者 Key
    if user_prof.api_key:
        active_engine = create_default_engine(api_key=user_prof.api_key)
    else:
        active_engine = default_engine

    search_res = active_engine.search_all_sources(user_prof)

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


# --- API 2: /api/fetch_enterprises (支持 GET & POST) ---
@app.api_route("/api/fetch_enterprises", methods=["GET", "POST"])
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


# --- API 3: /api/fetch_counselors (支持 GET & POST) ---
@app.api_route("/api/fetch_counselors", methods=["GET", "POST"])
def api_fetch_counselors(req: Optional[CounselorFetchRequest] = None):
    """【Tab 3】按省份和城市实时 Fetch 最新高校辅导员招聘公告与链接 (支持网页用户专属 API Key)"""
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prov = req.province if (req and req.province) else "all"
    city = req.city if (req and req.city) else "all"
    user_key = req.api_key if (req and req.api_key) else None

    anns = counselor_adapter.fetch_university_counselor_announcements(
        province=prov,
        city=city,
        batch_timestamp=batch_timestamp,
        api_key=user_key
    )

    db.save_counselor_announcements(anns, batch_timestamp=batch_timestamp)
    all_anns = db.get_all_counselor_announcements()

    response = {
        "status": "success",
        "fetched_at": batch_timestamp,
        "total_announcements": len(all_anns),
        "matched_count": len(anns),
        "counselors": all_anns
    }
    # 诚实空态:本批次未抓取到任何公告时明确告知,绝不编造数据充数
    if not anns:
        response["message"] = (
            f"暂未获取到【{prov}·{city}】的辅导员招聘公告。"
            "已返回历史数据；可尝试扩大查询范围（如 province=all）或稍后重试"
        )
    return response


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
