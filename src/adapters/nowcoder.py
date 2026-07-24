import uuid
from typing import List
from src.models import UserProfile, JobItem
from src.adapters.base import BaseJobSourceAdapter


class NowcoderAdapter(BaseJobSourceAdapter):
    """牛客网 (Nowcoder) 校招与实习岗位适配器"""

    @property
    def source_name(self) -> str:
        return "牛客网(Nowcoder)"

    def fetch_jobs(self, profile: UserProfile) -> List[JobItem]:
        kw = profile.keywords.split(",")[0].split()[0] if profile.keywords else "开发"
        loc = profile.location.split("/")[0] if "/" in profile.location else profile.location

        # 模拟牛客网实时校招日历与企业名企内推专场数据
        nowcoder_jobs = [
            JobItem(
                id=f"nc-{uuid.uuid4().hex[:6]}",
                title=f"{kw} 校招管培生/研发岗",
                company="美团",
                company_type="互联网大厂",
                company_size="10000人以上",
                salary="24k-38k·15.5薪",
                location=loc if loc != "全国" else "北京/上海/成都",
                batch=profile.batch,
                match_score=94,
                recommend_reason="牛客网校招热度榜 TOP3！核心到店/到家业务线招募，笔试通过率高，招募指标充足。",
                requirements=[
                    f"熟练掌握计算机基础与 {kw} 技术栈；",
                    "有互联网大厂实习经历或知名竞赛获奖优先；",
                    "逻辑清晰，具备强烈的责任心。"
                ],
                apply_url="https://zhaopin.meituan.com",
                tags=["牛客内推", "大厂热招", "包三餐", "成长极快"]
            ),
            JobItem(
                id=f"nc-{uuid.uuid4().hex[:6]}",
                title=f"{kw} 软件工程师 (校招直通车)",
                company="拼多多",
                company_type="互联网大厂",
                company_size="10000人以上",
                salary="30k-55k·18薪",
                location=loc if loc != "全国" else "上海",
                batch=profile.batch,
                match_score=92,
                recommend_reason="牛客网高薪薪资榜首选！提供业内顶尖薪酬竞争力与快速晋升通道。",
                requirements=[
                    "具备扎实的数据结构与算法基本功；",
                    "能够承担高强度高并发系统的研发挑战；",
                    "对技术有极致的技术追求。"
                ],
                apply_url="https://careers.pinduoduo.com",
                tags=["牛客爆款", "业内顶薪", "年终奖丰厚"]
            ),
            JobItem(
                id=f"nc-{uuid.uuid4().hex[:6]}",
                title=f"AI/算法研发工程师 ({kw}方向)",
                company="商汤科技 (SenseTime)",
                company_type="独角兽/AI头部",
                company_size="1000-5000人",
                salary="28k-45k·16薪",
                location=loc if loc != "全国" else "上海/北京",
                batch=profile.batch,
                match_score=89,
                recommend_reason="AI 独角兽企业，牛客学术讨论度高，学术与产业落地结合紧密。",
                requirements=[
                    "熟悉 PyTorch/TensorFlow 等主流深度学习框架；",
                    "有 CCF 推荐会议论文或知名 AI 竞赛 Top 经历者优先；",
                    "具备良好的英文技术文献阅读能力。"
                ],
                apply_url="https://hr.sensetime.com",
                tags=["牛客推荐", "AI独角兽", "弹性工作", "前沿技术"]
            )
        ]

        return nowcoder_jobs
