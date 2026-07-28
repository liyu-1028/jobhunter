"""辅导员公告查询 Facade.

保留旧版 CounselorJobAdapter 的公开方法签名, server.py / cli.py / tests
无需任何改动; 内部委托 CounselorAggregator 完成:
多源并发抓取 → 四层校验管线 → 增强指纹去重.

与旧版的关键区别: 任何环节都不再编造公告数据,
无结果时诚实返回空列表 (见 docs/design_counselor_engine_refactor.md).
"""

from typing import Dict, List, Optional

from src.models import UniversityCounselorAnnouncement
from src.registry.university_registry import UniversityRegistry
from src.adapters.counselor_aggregator import CounselorAggregator
from src.adapters.counselor_base import RawAnnouncement  # noqa: F401  (便于外部类型引用)
from src.adapters.counselor_bing import BingSiteSearchSource
from src.adapters.counselor_curated import CuratedSource
from src.adapters.counselor_gaoxiaojob import GaoxiaojobSource


class CounselorJobAdapter:
    """兼容旧接口的多源辅导员公告查询适配器."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.registry = UniversityRegistry.load()
        self._bing = BingSiteSearchSource()
        self.aggregator = CounselorAggregator(
            sources=[self._bing, GaoxiaojobSource(), CuratedSource()],
            registry=self.registry,
            api_key=api_key,
        )

    def fetch_search_snippets(self, province: str = "all", city: str = "all") -> List[Dict[str, str]]:
        """[兼容旧接口] 返回 Bing 搜索摘要 [{title, snippet, url}].

        无结果时返回空列表, 不再生成任何编造的兜底摘要.
        """
        return self._bing.fetch_snippets(province, city, self.registry)

    def fetch_university_counselor_announcements(
        self,
        province: str = "all",
        city: str = "all",
        batch_timestamp: str = None,
        api_key: Optional[str] = None,
    ) -> List[UniversityCounselorAnnouncement]:
        """多源并发抓取并按校验管线提取辅导员招聘公告."""
        return self.aggregator.run(
            province=province,
            city=city,
            batch_timestamp=batch_timestamp,
            api_key=api_key or self.api_key,
        )
