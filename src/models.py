from pydantic import BaseModel, Field
from typing import List, Optional

class UserProfile(BaseModel):
    degree: str = "硕士"
    school: str = "双一流"
    major: str = "计算机"
    batch: str = "2026届秋招"
    target_industry: str = "互联网"
    company_type: str = "大厂/国企"
    company_size: str = "1000人以上"
    location: str = "杭州"
    keywords: str = "Python, 大模型"
    api_key: Optional[str] = None  # 用户专属 API Key

class JobItem(BaseModel):
    id: str
    title: str
    company: str
    company_type: str = "国企"
    company_size: str = "1000人以上"
    location: str
    salary: str = "面议"
    batch: str = "2026届秋招"
    match_score: int = 85
    recommend_reason: str
    requirements: List[str] = []
    tags: List[str] = []
    apply_url: str = "#"
    source: str = "deepseek"
    fetched_at: str = ""  # 查询批次时间戳

class UniversityCounselorAnnouncement(BaseModel):
    id: str
    university: str                   # 高校名称
    university_level: str = "双一流"    # 985/211/双一流/省属重点
    province: str                     # 省份
    city: str                         # 城市
    has_announcement: bool = True     # 是否发布公告
    announcement_status: str = "🟢 已发布招聘公告" # 状态描述
    announcement_title: str           # 公告标题
    publish_date: str = ""            # 发布时间
    announcement_url: str = "#"       # 公告/人事处链接
    requirements_summary: str = ""    # 选拔章程/要求简述
    fetched_at: str = ""              # 查询批次时间戳

class SearchResult(BaseModel):
    search_time: str
    total_found: int
    jobs: List[JobItem]
