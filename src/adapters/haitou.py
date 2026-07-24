import uuid
from typing import List
from src.models import UserProfile, JobItem
from src.adapters.base import BaseJobSourceAdapter


class HaitouAdapter(BaseJobSourceAdapter):
    """海投网 (Haitou) 校招与宣讲会岗位适配器"""

    @property
    def source_name(self) -> str:
        return "海投网(Haitou)"

    def fetch_jobs(self, profile: UserProfile) -> List[JobItem]:
        kw = profile.keywords.split(",")[0].split()[0] if profile.keywords else "开发"
        loc = profile.location.split("/")[0] if "/" in profile.location else profile.location

        # 模拟海投网校招与宣讲会聚合数据
        haitou_jobs = [
            JobItem(
                id=f"ht-{uuid.uuid4().hex[:6]}",
                title=f"软件研发工程师 ({kw})",
                company="网易集团 (Netease)",
                company_type="互联网大厂",
                company_size="10000人以上",
                salary="22k-36k·16薪",
                location=loc if loc != "全国" else "杭州/广州",
                batch=profile.batch,
                match_score=93,
                recommend_reason="海投网宣讲会关注度前三！网易雷火/互娱核心研发岗位，食堂福利极佳。",
                requirements=[
                    f"计算机相关专业毕业，精通 {kw} 或 C++/Java 开发；",
                    "对互联网业务或游戏研发有浓厚兴趣；",
                    "具备强烈的自我驱动力。"
                ],
                apply_url="https://hr.163.com",
                tags=["海投热门", "免费猪厂食堂", "六险一金"]
            ),
            JobItem(
                id=f"ht-{uuid.uuid4().hex[:6]}",
                title=f"金融科技/软件工程师",
                company="招商银行网络科技",
                company_type="国企/金融科技",
                company_size="5000-10000人",
                salary="18k-30k·16薪",
                location=loc if loc != "全国" else "深圳/杭州",
                batch=profile.batch,
                match_score=87,
                recommend_reason="海投网国企/金融科技板块好评度高，福利稳定，工作节奏相对适中。",
                requirements=[
                    "本科及以上学历，计算机或软件工程相关专业；",
                    "熟悉软件工程规范与单元测试；",
                    "具备良好的沟通和团队合作意识。"
                ],
                apply_url="https://career.cmbchina.com",
                tags=["海投国企", "金融科技", "稳定福利", "带薪年假"]
            )
        ]

        return haitou_jobs
