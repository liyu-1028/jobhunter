from typing import List, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户求职个人信息与偏好"""
    degree: str = Field(description="学历，如：本科、硕士、博士")
    school: str = Field(description="学校名称")
    major: Optional[str] = Field(default="", description="专业名称")
    batch: str = Field(description="招聘批次，如：2026届秋招、2026届春招、社招")
    target_industry: str = Field(description="目标行业，如：互联网、金融、芯片")
    company_type: str = Field(description="公司性质，如：国企、外企、大厂、独角兽")
    company_size: str = Field(description="公司人数/规模，如：1000人以上、500-1000人")
    location: str = Field(default="全国", description="期望工作城市")
    keywords: str = Field(description="搜索岗位关键词，如：Python后端、大模型工程师")


class JobItem(BaseModel):
    """岗位详情模型"""
    id: str = Field(description="岗位唯一标识号")
    title: str = Field(description="岗位名称")
    company: str = Field(description="公司名称")
    company_type: str = Field(description="公司性质，如：国企、外企、上市公司")
    company_size: str = Field(description="公司规模人数")
    salary: str = Field(description="薪资范围，如：25k-40k·16薪")
    location: str = Field(description="工作地点/城市")
    batch: str = Field(description="招聘批次")
    match_score: int = Field(description="匹配度评分 (0-100)")
    recommend_reason: str = Field(description="大模型推荐理由与匹配亮点")
    requirements: List[str] = Field(default_factory=list, description="核心岗位要求列表")
    apply_url: str = Field(description="官方投递链接或招聘渠道")
    tags: List[str] = Field(default_factory=list, description="岗位标签，如：[双休, 免费三餐, 不限经验]")


class SearchResult(BaseModel):
    """全量搜索分析结果模型"""
    search_time: str = Field(description="搜索生成时间")
    profile: UserProfile = Field(description="用户求职 Profile")
    jobs: List[JobItem] = Field(default_factory=list, description="匹配到的岗位列表")
    summary: str = Field(default="", description="大模型给出的整体求职策略与市场行情建议")
