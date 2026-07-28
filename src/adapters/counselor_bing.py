"""Bing 搜索数据源 — 名录驱动的定向搜索.

由旧版 cn.bing.com 抓取逻辑重构而来:
- query 不再依赖手写 CITY_UNIVERSITY_MAP, 而由 UniversityRegistry 按省/市展开;
- 增加超时重试与指数退避;
- 无结果时诚实返回空列表, 绝不编造兜底数据 (旧版致命缺陷 D4 的根除点).
"""

import urllib.parse
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from src.adapters.counselor_base import (
    BaseCounselorSource,
    RawAnnouncement,
    DEFAULT_HEADERS,
    get_with_retry,
)
from src.registry.university_registry import UniversityRegistry, normalize_region


class BingSiteSearchSource(BaseCounselorSource):
    """Bing 搜索结果页抓取源 (HTML 结构脆弱, 定位为补充源)."""

    def __init__(self, max_universities: int = 3, max_queries: int = 4):
        self.headers = dict(DEFAULT_HEADERS)
        self.max_universities = max_universities
        self.max_queries = max_queries

    @property
    def source_name(self) -> str:
        return "bing"

    def build_queries(self, province: str, city: str, registry: UniversityRegistry) -> List[str]:
        """基于高校名录生成精准 query 组 (替代旧版手写映射表)."""
        prov = normalize_region(province) if province not in (None, "all") else ""
        c = normalize_region(city) if city not in (None, "all") else ""

        queries: List[str] = []
        universities = registry.list_by(province=province or "all", city=city or "all")
        for uni in universities[: self.max_universities]:
            queries.append(f"{uni['name']} 辅导员 招聘")

        if c:
            queries.append(f"{prov} {c} 高校 辅导员 招聘 公告".strip())
            queries.append(f"{c} 大学 辅导员 招聘")
        elif prov:
            queries.append(f"{prov} 高校 辅导员 招聘 公告")

        if not queries:
            queries.append("高校 辅导员 招聘 公告 2026 2027")

        return queries[: self.max_queries]

    def fetch_snippets(
        self,
        province: str = "all",
        city: str = "all",
        registry: Optional[UniversityRegistry] = None,
    ) -> List[Dict[str, str]]:
        """抓取搜索摘要列表 [{title, snippet, url}] — 兼容旧版返回格式."""
        registry = registry or UniversityRegistry.load()
        queries = self.build_queries(province, city, registry)
        snippets: List[Dict[str, str]] = []
        seen_urls = set()

        for kw in queries:
            url = f"https://cn.bing.com/search?q={urllib.parse.quote(kw)}"
            resp = get_with_retry(url, headers=self.headers, timeout=8, retries=1)
            if resp is None:
                continue
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.find_all("li", class_="b_algo"):
                    h2 = item.find("h2")
                    link = h2.find("a") if h2 else None
                    snippet_el = item.find("p") or item.find("div", class_="b_caption")
                    if not (h2 and link):
                        continue
                    href = link.get("href", "")
                    if not href.startswith("http") or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    snippets.append({
                        "title": h2.get_text(strip=True),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "url": href,
                    })
            except Exception as e:  # noqa: BLE001 — 解析失败只跳过本页
                print(f"⚠️ Bing 结果解析异常: {e}")

        if not snippets:
            print(f"ℹ️ Bing 未获取到结果 (province={province}, city={city})，不再编造兜底数据")
        return snippets

    def fetch(self, province: str = "all", city: str = "all", registry=None) -> List[RawAnnouncement]:
        snippets = self.fetch_snippets(province, city, registry)
        return [
            RawAnnouncement(
                title=s["title"],
                url=s["url"],
                snippet=s["snippet"],
                source=self.source_name,
            )
            for s in snippets
        ]
