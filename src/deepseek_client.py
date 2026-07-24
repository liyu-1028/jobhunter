import os
import json
import uuid
from datetime import datetime
from typing import Optional
from openai import OpenAI
from src.models import UserProfile, JobItem, SearchResult


class DeepSeekJobHunter:
    """DeepSeek 大模型岗位搜索与匹配引擎"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def search_jobs(self, profile: UserProfile, mock_if_no_key: bool = True) -> SearchResult:
        """根据求职 Profile 调用 DeepSeek 检索并返回匹配岗位结果"""
        
        if not self.client and not mock_if_no_key:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请在 .env 文件中配置或直接传入 API Key。")

        if not self.client:
            # 开启 Demo Mock 模式，生成贴合用户 Profile 的样例真实岗位
            return self._generate_mock_results(profile)

        system_prompt = """你是一位资深的专业猎头和 HR 招聘大模型专家。
你的任务是根据求职者提供的个人背景（学历、学校、批次）和偏好（行业、公司性质、规模、城市、关键词），检索、匹配并评估当前市场上最符合条件的优质招聘岗位。

请严格返回符合以下 JSON 结构的标准 JSON 对象（不要包裹 Markdown ```json ...``` 标记）：
{
  "summary": "针对该求职者背景的整体市场行情分析与投递策略建议 (150字左右)",
  "jobs": [
    {
      "id": "job-1",
      "title": "岗位名称",
      "company": "公司名称",
      "company_type": "公司性质（如：国企/外企/互联网大厂/独角兽）",
      "company_size": "公司规模（如：1000人以上）",
      "salary": "薪资范围（如：25k-45k·16薪）",
      "location": "工作地点",
      "batch": "招聘批次（如：2026届秋招）",
      "match_score": 95,
      "recommend_reason": "核心推荐理由与优势匹配分析",
      "requirements": ["岗位要求1", "岗位要求2", "岗位要求3"],
      "apply_url": "官方投递链接或招聘网申地址",
      "tags": ["核心亮点标签1", "标签2", "标签3"]
    }
  ]
}

要求：
1. 匹配度评分 (match_score) 为 0-100 的整数，越符合求职者条件越接近 100 分。
2. 尽可能提供真实有效的公司招聘项目、网申链接（若无法提供具体动态链接，可提供公司官网网申入口）。
3. 岗位不少于 6-10 个，且覆盖不同层次的匹配梯度（如保底、冲刺、精选）。
"""

        user_prompt = f"""求职者个人背景与期望条件如下：
- 学历: {profile.degree}
- 院校名称: {profile.school}
- 专业: {profile.major or '未指定'}
- 招聘批次: {profile.batch}
- 期望目标行业: {profile.target_industry}
- 期望公司性质: {profile.company_type}
- 期望公司规模: {profile.company_size}
- 期望工作地点: {profile.location}
- 搜索岗位关键词: {profile.keywords}

请分析并检索匹配该求职者的优质岗位列表，并按照要求输出 JSON。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            jobs = []
            for idx, raw_job in enumerate(data.get("jobs", [])):
                job_id = raw_job.get("id") or f"job-{uuid.uuid4().hex[:8]}"
                jobs.append(JobItem(
                    id=job_id,
                    title=raw_job.get("title", "未命名岗位"),
                    company=raw_job.get("company", "知名企业"),
                    company_type=raw_job.get("company_type", profile.company_type),
                    company_size=raw_job.get("company_size", profile.company_size),
                    salary=raw_job.get("salary", "面议"),
                    location=raw_job.get("location", profile.location),
                    batch=raw_job.get("batch", profile.batch),
                    match_score=int(raw_job.get("match_score", 85)),
                    recommend_reason=raw_job.get("recommend_reason", "符合求职意向与技术栈。"),
                    requirements=raw_job.get("requirements", []),
                    apply_url=raw_job.get("apply_url", "https://campus.example.com"),
                    tags=raw_job.get("tags", ["热招中", "急聘"])
                ))

            # 按匹配度降序排列
            jobs.sort(key=lambda x: x.match_score, reverse=True)

            return SearchResult(
                search_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                profile=profile,
                jobs=jobs,
                summary=data.get("summary", "大模型已完成岗位深度匹配分析。")
            )

        except Exception as e:
            print(f"\n⚠️ 调用 DeepSeek API 发生错误: {e}")
            print("💡 自动切换为智能 Demo 数据生成模式...")
            return self._generate_mock_results(profile)

    def _generate_mock_results(self, profile: UserProfile) -> SearchResult:
        """未配置 API Key 或 API 异常时的智能 Mock 数据生成"""
        kw = profile.keywords.split(",")[0].split()[0] if profile.keywords else "开发"
        loc = profile.location.split("/")[0] if "/" in profile.location else profile.location
        
        mock_jobs = [
            JobItem(
                id="job-mock-1",
                title=f"{kw} 研发工程师",
                company="腾讯科技",
                company_type="互联网大厂",
                company_size="10000人以上",
                salary="25k-40k·16薪",
                location=loc if loc != "全国" else "深圳/北京",
                batch=profile.batch,
                match_score=96,
                recommend_reason=f"匹配度极高！{profile.school}{profile.degree}背景非常符合腾讯校园招聘选拔标准，部门核心业务拓展中，急需{kw}相关人才。",
                requirements=[
                    f"熟练掌握 {kw} 相关核心原理与框架，具备良好的代码功底；",
                    "熟悉分布式系统设计、高并发与数据库性能调优；",
                    "具备良好的沟通协调能力和团队协作意识。"
                ],
                apply_url="https://join.qq.com",
                tags=["985/211偏好", "大厂核心部门", "六险一金", "免费早餐"]
            ),
            JobItem(
                id="job-mock-2",
                title=f"高级 {kw} 专家 / 架构师",
                company="阿里巴巴",
                company_type="互联网大厂",
                company_size="10000人以上",
                salary="30k-50k·15薪",
                location=loc if loc != "全国" else "杭州",
                batch=profile.batch,
                match_score=93,
                recommend_reason=f"阿里云/淘天集团重点招募团队，对{profile.degree}学历背景有明确人才梯队偏好，发展空间大。",
                requirements=[
                    "深入理解计算架构与软硬件协同优化；",
                    "有大型项目开发经验者优先；",
                    "思维敏捷，对新技术有极高的热情。"
                ],
                apply_url="https://talent.alibaba.com",
                tags=["股票期权", "带薪年假", "餐补补贴"]
            ),
            JobItem(
                id="job-mock-3",
                title=f"大模型与 AI 平台工程师 ({kw})",
                company="字节跳动",
                company_type="独角兽/大厂",
                company_size="10000人以上",
                salary="35k-60k·15薪",
                location=loc if loc != "全国" else "北京/上海",
                batch=profile.batch,
                match_score=91,
                recommend_reason="AI Lab 核心项目组，技术氛围极佳，提供极致的算力资源与前沿大模型落地场景。",
                requirements=[
                    "精通 Python/C++ 及主流深度学习/大模型推理框架；",
                    "具备强悍的算法基础与 Data Structure 能力；",
                    "优秀的 Problem Solving 能力。"
                ],
                apply_url="https://jobs.bytedance.com",
                tags=["租房补贴", "免费三餐", "极客氛围", "扁平管理"]
            ),
            JobItem(
                id="job-mock-4",
                title=f"软件研发工程师 ({profile.target_industry}方向)",
                company="华为技术有限公司",
                company_type="行业龙头/民企",
                company_size="10000人以上",
                salary="22k-38k·18薪",
                location=loc if loc != "全国" else "深圳/南京",
                batch=profile.batch,
                match_score=88,
                recommend_reason=f"华为 2012 实验室重点项目，认可{profile.school}的学术与工程培养质量，薪资给力。",
                requirements=[
                    "扎实的计算机基础（操作系统、网络、数据结构）；",
                    "良好的项目实践经历或竞赛获奖优先；",
                    "适应高强度研发挑战。"
                ],
                apply_url="https://career.huawei.com",
                tags=["年终奖丰厚", "全球化视野", "完善培训系统"]
            ),
            JobItem(
                id="job-mock-5",
                title=f"数字化研发工程师",
                company="中国移动研究院",
                company_type="国企/央企",
                company_size="5000-10000人",
                salary="18k-28k·16薪",
                location=loc if loc != "全国" else "北京/广州",
                batch=profile.batch,
                match_score=86,
                recommend_reason=f"央企编制，工作生活平衡(WLB)。对{profile.degree}学历有良好的定级与落户补贴政策。",
                requirements=[
                    "计算机、软件工程或电子信息类相关专业；",
                    "了解云计算、大数据或人工智能应用；",
                    "政治素养过硬，具备良好的文档撰写能力。"
                ],
                apply_url="https://job.10086.cn",
                tags=["央企编制", "解决落户", "工作生活平衡", "补充医疗保险"]
            ),
            JobItem(
                id="job-mock-6",
                title=f"核心系统研发工程师",
                company="微软 (Microsoft China)",
                company_type="外企",
                company_size="5000-10000人",
                salary="28k-42k·14薪",
                location=loc if loc != "全国" else "苏州/北京",
                batch=profile.batch,
                match_score=84,
                recommend_reason="知名外企，严格遵循 955 工作制，英语环境良好，适合注重工作生活平衡与国际化视野的同学。",
                requirements=[
                    "具备良好的英文读写与口语交流能力；",
                    "精通数据结构与算法分析；",
                    "注重代码质量与单元测试覆盖。"
                ],
                apply_url="https://careers.microsoft.com",
                tags=["WLB955", "不加班", "15天带薪年假", "顶级福利"]
            )
        ]

        return SearchResult(
            search_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            profile=profile,
            jobs=mock_jobs,
            summary=f"针对您的【{profile.school}·{profile.degree}】背景及在【{profile.target_industry}】领域的期望，目前{profile.batch}市场整体需求热度高。大厂与国企均对您的匹配度表现优秀。建议优先投递匹配度 90+ 的大厂核心岗位，同时搭配 1-2 家央企国企作为稳健选择。"
        )
