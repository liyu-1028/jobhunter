"""人工收录公告数据源.

数据来自 data/curated_announcements.json (由旧版 NATIONWIDE_UNIVERSITY_DATABASE
硬编码迁移而来), 以 "📌 人工收录" 身份展示, 与实时抓取结果明确区分.
严禁由代码自动扩充该文件 —— 只允许人工编辑.
"""

import os
import json
from typing import List

from src.adapters.counselor_base import BaseCounselorSource, RawAnnouncement, PROJECT_ROOT

DEFAULT_CURATED_PATH = os.path.join(PROJECT_ROOT, "data", "curated_announcements.json")


def _region_match(expected: str, actual: str) -> bool:
    if not expected or expected == "all":
        return True
    e = expected.replace("省", "").replace("市", "").strip()
    actual = (actual or "").strip()
    return bool(e) and bool(actual) and (e in actual or actual in e)


class CuratedSource(BaseCounselorSource):
    """人工收录的历史公告数据 (已人工核实, 免关键词预过滤)."""

    def __init__(self, data_path: str = None):
        self.data_path = data_path or DEFAULT_CURATED_PATH
        self._records = None

    @property
    def source_name(self) -> str:
        return "curated"

    def _load(self) -> List[dict]:
        if self._records is None:
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._records = [r for r in loaded if isinstance(r, dict)] if isinstance(loaded, list) else []
            except (OSError, json.JSONDecodeError) as e:
                print(f"⚠️ 人工收录数据加载失败: {e}")
                self._records = []
        return self._records

    def fetch(self, province: str = "all", city: str = "all", registry=None) -> List[RawAnnouncement]:
        raws: List[RawAnnouncement] = []
        for rec in self._load():
            if not _region_match(province, rec.get("province", "")):
                continue
            if not _region_match(city, rec.get("city", "")):
                continue
            raws.append(RawAnnouncement(
                title=rec.get("announcement_title", ""),
                url=rec.get("announcement_url", ""),
                snippet=rec.get("requirements_summary", ""),
                publish_date=rec.get("publish_date", ""),
                source=self.source_name,
                meta=rec,
            ))
        return raws
