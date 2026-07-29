"""岗位搜索 Facade — 替代旧版 create_default_engine 的三假源组装.

方法签名与旧版 MultiSourceJobEngine.search_all_sources 保持一致,
src/engine.py 的 create_default_engine 工厂返回本类实例,
server.py / cli.py 的调用点零改动.
"""

from datetime import datetime
from typing import Optional

from src.models import UserProfile, SearchResult
from src.adapters.job_aggregator import JobAggregator
from src.adapters.serper_source import SerperSearchSource
from src.adapters.tavily_source import TavilySearchSource


class JobSearchAdapter:
    """多源岗位搜索 Facade: Serper + Tavily 真实搜索 + 五层校验管线."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.aggregator = JobAggregator(
            sources=[SerperSearchSource(), TavilySearchSource()],
            api_key=api_key,
        )

    def search_all_sources(self, profile: UserProfile) -> SearchResult:
        """并发抓取并校验岗位, 返回与旧引擎同构的 SearchResult."""
        jobs = self.aggregator.run(profile)
        return SearchResult(
            search_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_found=len(jobs),
            jobs=jobs,
        )
