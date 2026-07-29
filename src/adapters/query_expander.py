"""用户多维 Profile → 多组搜索 query 展开器.

将 UserProfile 的学历/批次/行业/公司性质/城市/关键词等多维条件
展开为覆盖不同搜索意图的 query 组, 实现「全面搜索岗位或公司的条件」.
"""

from typing import List

from src.models import UserProfile

# 大厂官网定向搜索域名 (site: 语法)
BIG_TECH_DOMAINS = ("join.qq.com", "talent.alibaba.com", "jobs.bytedance.com")


class QueryExpander:
    """四策略 query 展开: 精准 × 泛匹配 × 校友内推 × 大厂定向."""

    MAX_QUERIES = 12

    def expand(self, profile: UserProfile) -> List[str]:
        keywords = [k.strip() for k in (profile.keywords or "").split(",") if k.strip()]
        locations = [loc.strip() for loc in (profile.location or "").split("/") if loc.strip()]

        queries: List[str] = []

        # 策略 1: 关键词 × 城市 × 批次 (精准匹配)
        for kw in keywords[:3]:
            if locations:
                for loc in locations[:2]:
                    queries.append(f"{kw} {loc} {profile.batch} 招聘")
            else:
                queries.append(f"{kw} {profile.batch} 招聘")

        # 策略 2: 行业 × 公司性质 (泛匹配)
        queries.append(f"{profile.target_industry} {profile.company_type} {profile.batch} 招聘")

        # 策略 3: 学校 + 内推 (校友网络)
        if profile.school:
            queries.append(f"{profile.school} {profile.batch} 内推")

        # 策略 4: 大厂官网定向 (site: 语法)
        first_kw = keywords[0] if keywords else "研发"
        for domain in BIG_TECH_DOMAINS:
            queries.append(f"site:{domain} {first_kw} {profile.batch}")

        # 去重 (保持顺序) + 总量封顶, 保护搜索 API 配额
        seen, out = set(), []
        for q in queries:
            normalized = " ".join(q.split())
            if normalized and normalized not in seen:
                seen.add(normalized)
                out.append(normalized)
        return out[: self.MAX_QUERIES]
