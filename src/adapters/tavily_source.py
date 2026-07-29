"""Tavily (api.tavily.com) LLM 友好搜索 API 数据源.

免费额度: 1,000 次/月。返回清洗后的网页正文片段 (content 字段),
天然适合 LLM 二次结构化提取, query 消耗量较 Serper 更节制.
"""

import os
from typing import List, Optional

from src.models import UserProfile
from src.adapters.job_base import BaseJobSource, RawJob, post_with_retry

TAVILY_ENDPOINT = "https://api.tavily.com/search"


class TavilySearchSource(BaseJobSource):
    """面向 LLM 的搜索 API 适配器 (防御式实现, 异常静默降级)."""

    max_queries = 4

    def __init__(self, api_key: Optional[str] = None, max_results: int = 5):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.max_results = max_results
        self._warned = False

    @property
    def source_name(self) -> str:
        return "tavily"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def fetch(self, queries: List[str], profile: UserProfile = None) -> List[RawJob]:
        if not self.available:
            if not self._warned:
                print("ℹ️ 未配置 TAVILY_API_KEY, Tavily 数据源跳过")
                self._warned = True
            return []

        raws: List[RawJob] = []
        seen_urls = set()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        for query in queries[: self.max_queries]:
            try:
                resp = post_with_retry(
                    TAVILY_ENDPOINT,
                    json_body={
                        "query": query,
                        "max_results": self.max_results,
                        "search_depth": "basic",
                    },
                    headers=headers,
                    timeout=15,
                    retries=1,
                )
                if resp is None:
                    continue
                data = resp.json()
                for item in data.get("results") or []:
                    url = (item.get("url") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not url or not title or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    raws.append(RawJob(
                        title=title,
                        url=url,
                        snippet=(item.get("content") or "").strip()[:500],
                        publish_date=item.get("published_date") or "",
                        source=self.source_name,
                        meta={"query": query, "score": item.get("score")},
                    ))
            except Exception as e:  # noqa: BLE001 — 单 query 失败不阻塞整体
                print(f"⚠️ Tavily 查询异常 [{query}]: {e}")

        return raws
