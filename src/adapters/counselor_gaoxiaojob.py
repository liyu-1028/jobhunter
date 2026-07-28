"""高校人才网 (gaoxiaojob.com) 辅导员频道数据源.

⚠️ 重要: 下方频道 URL / 省份 slug / 列表页选择器来自调研报告推测,
均标注 [需验证], 上线前必须用浏览器核实实际页面结构 (并检查 robots.txt).
在未验证或页面改版时, 本源静默降级为空列表, 绝不阻塞其他数据源.
"""

import urllib.parse
from typing import List

from bs4 import BeautifulSoup

from src.adapters.counselor_base import (
    BaseCounselorSource,
    RawAnnouncement,
    DEFAULT_HEADERS,
    COUNSELOR_KEYWORDS,
    get_with_retry,
)

BASE_URL = "https://www.gaoxiaojob.com"


class GaoxiaojobSource(BaseCounselorSource):
    """高校人才网辅导员招聘频道适配器 (防御式实现)."""

    CHANNEL_PATH = "/zhaopin/fudaoyuan/"              # [需验证] 辅导员频道路径
    PROVINCE_SLUGS = {                                # [需验证] 省份拼音 slug
        "安徽": "anhui", "江苏": "jiangsu", "浙江": "zhejiang", "广东": "guangdong",
        "北京": "beijing", "上海": "shanghai", "湖北": "hubei", "湖南": "hunan",
        "四川": "sichuan", "山东": "shandong", "陕西": "shaanxi", "河南": "henan",
    }
    LIST_SELECTORS = (                                # [需验证] 候选列表选择器
        "div.article-list li",
        "ul.news-list li",
        "div.list-content li",
        "div.right-list li",
    )

    def __init__(self, max_items: int = 30):
        self.headers = {**DEFAULT_HEADERS, "Referer": BASE_URL + "/"}
        self.max_items = max_items

    @property
    def source_name(self) -> str:
        return "Gaoxiaojob"

    def _channel_url(self, province: str) -> str:
        prov = (province or "").replace("省", "").replace("市", "").strip()
        slug = self.PROVINCE_SLUGS.get(prov) if prov not in ("", "all") else None
        return BASE_URL + (f"{self.CHANNEL_PATH}{slug}/" if slug else self.CHANNEL_PATH)

    def fetch(self, province: str = "all", city: str = "all", registry=None) -> List[RawAnnouncement]:
        url = self._channel_url(province)
        try:
            resp = get_with_retry(url, headers=self.headers, timeout=10, retries=1)
            if resp is None:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            raws: List[RawAnnouncement] = []
            seen_urls = set()

            for selector in self.LIST_SELECTORS:
                for li in soup.select(selector):
                    anchor = li.find("a", href=True)
                    if not anchor:
                        continue
                    title = anchor.get_text(strip=True)
                    href = urllib.parse.urljoin(BASE_URL + "/", anchor["href"])
                    if not title or href in seen_urls:
                        continue
                    # 仅保留标题命中辅导员关键词的条目
                    if not any(kw in title for kw in COUNSELOR_KEYWORDS):
                        continue
                    seen_urls.add(href)
                    date_el = li.find("span") or li.find("em")
                    raws.append(RawAnnouncement(
                        title=title,
                        url=href,
                        snippet=li.get_text(" ", strip=True),
                        publish_date=date_el.get_text(strip=True) if date_el else "",
                        source=self.source_name,
                    ))
                    if len(raws) >= self.max_items:
                        return raws
                if raws:
                    break  # 命中一个选择器即可, 不再尝试其余

            if not raws:
                print("ℹ️ 高校人才网频道无命中 (页面结构可能已变更, 参见 [需验证] 标注)")
            return raws
        except Exception as e:  # noqa: BLE001 — 整源降级, 不阻塞管线
            print(f"⚠️ 高校人才网数据源异常 (降级为空列表): {e}")
            return []
