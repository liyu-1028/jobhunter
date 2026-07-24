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

class CounselorJobItem(BaseModel):
    id: str
    university: str
    province: str
    city: str
    title: str = "专职辅导员"
    establishment_type: str = "事业编制"  # 事业编制 / 员额制 / 合同制
    salary: str = "10-15万/年"
    requirements: List[str] = []
    apply_url: str = "#"
    status: str = "🟢 招聘中"
    fetched_at: str = ""  # 批次时间戳

class SearchResult(BaseModel):
    search_time: str
    total_found: int
    jobs: List[JobItem]
