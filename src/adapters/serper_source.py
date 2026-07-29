"""Serper (google.serper.dev) Google 搜索 JSON API 数据源.

免费额度: 注册送 2,500 次 (一次性, 6 个月有效); 付费约 $1/1000 次.
返回结构化 Google SERP JSON (organic 结果含 title/link/snippet/date).
"""

import os
from typing import List, Optional

from src.models import UserProfile
from src.adapters.job_base import BaseJobSource, RawJob, post_with_retry

SERPER_ENDPOINT = "https://google.serper.dev/search"


class SerperSearchSource(BaseJobSource):
    """Google 搜索结果 API 适配器 (防御式实现, 异常静默降级)."""

    max_queries = 8

    def __init__(self, api_key: Optional[str] = None, num: int = 10):
        self.api_key = api_key or os.getenv("SERPER_API_KEY", "")
        self.num = num
        self._warned = False

    @property
    def source_name(self) -> str:
        return "serper"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def fetch(self, queries: List[str], profile: UserProfile = None) -> List[RawJob]:
        if not self.available:
            if not self._warned:
                print("ℹ️ 未配置 SERPER_API_KEY, Serper 数据源跳过")
                self._warned = True
            return []

        raws: List[RawJob] = []
        seen_urls = set()
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        for query in queries[: self.max_queries]:
            try:
                resp = post_with_retry(
                    SERPER_ENDPOINT,
                    json_body={"q": query, "num": self.num, "gl": "cn", "hl": "zh-cn"},
                    headers=headers,
                    timeout=10,
                    retries=1,
                )
                if resp is None:
                    continue
                data = resp.json()
                for item in data.get("organic") or []:
                    link = (item.get("link") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not link or not title or link in seen_urls:
                        continue
                    seen_urls.add(link)
                    raws.append(RawJob(
                        title=title,
                        url=link,
                        snippet=(item.get("snippet") or "").strip(),
                        publish_date=item.get("date") or "",
                        source=self.source_name,
                        meta={"query": query},
                    ))
            except Exception as e:  # noqa: BLE001 — 单 query 失败不阻塞整体
                print(f"⚠️ Serper 查询异常 [{query}]: {e}")

        return raws
