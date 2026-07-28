"""辅导员公告多源聚合器 — 并发抓取 + 四层校验管线.

校验管线 (逐层丢弃脏数据):
① 关键词预过滤 (人工收录源豁免, 因其为人工核实数据);
② 结构化提取: 有 LLM Key 走 DeepSeek JSON 提取, 否则无损直接映射;
③ URL 溯源: 公告链接必须等于原始抓取链接 (LLM 永不产出 URL);
④ 名录验证: 高校名必须能匹配 UniversityRegistry, 匹配信息回填省/市;
⑤ 增强指纹去重 (高校|标题|归一化URL|来源).
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional

from src.models import UniversityCounselorAnnouncement
from src.deepseek_client import DeepSeekJobHunter
from src.adapters.counselor_base import (
    BaseCounselorSource,
    RawAnnouncement,
    COUNSELOR_KEYWORDS,
    fingerprint,
)
from src.registry.university_registry import UniversityRegistry

_LLM_SYSTEM_PROMPT = """你是一个高校辅导员招聘公告结构化提取专家。
请从给定的公告数据中提取字段，严格输出 JSON（不要包裹 markdown 代码块）：
{
  "has_announcement": true,
  "university": "高校官方全称",
  "university_level": "院校层次(985/211/双一流/省属重点/高职等)",
  "announcement_title": "公告完整标题",
  "publish_date": "发布日期(YYYY-MM-DD，无法确定时输出空字符串)",
  "requirements_summary": "选拔要求简述(政治面貌、学历、编制等)"
}
规则：
1. 不要输出任何 URL / 链接字段，链接由系统统一回填；
2. 如果输入内容不是高校辅导员招聘公告，返回 {"has_announcement": false}；
3. university 使用官方全称，无法判断时返回空字符串。"""


class CounselorAggregator:
    """多源聚合器: 替代旧版单适配器抓取+提取+兜底一体化实现."""

    def __init__(
        self,
        sources: List[BaseCounselorSource],
        registry: UniversityRegistry,
        api_key: Optional[str] = None,
    ):
        self.sources = sources
        self.registry = registry
        self.api_key = api_key

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def run(
        self,
        province: str = "all",
        city: str = "all",
        batch_timestamp: str = None,
        api_key: Optional[str] = None,
    ) -> List[UniversityCounselorAnnouncement]:
        batch_timestamp = batch_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_all = self._collect(province, city)

        llm = DeepSeekJobHunter(api_key=api_key or self.api_key)
        results: List[UniversityCounselorAnnouncement] = []
        seen_ids = set()

        for raw in raw_all:
            # ① 预过滤 (人工收录源豁免)
            if raw.source != "curated" and not self._prefilter(raw):
                continue
            # ② 结构化提取
            ann = self._extract(raw, province, city, batch_timestamp, llm)
            if ann is None:
                continue
            # ③ URL 溯源: 链接只能来自原始抓取结果
            if ann.announcement_url != raw.url:
                print(f"ℹ️ 丢弃: URL 不可溯源 → {ann.announcement_url}")
                continue
            # ④ 名录验证与省/市回填
            uni = self.registry.match(ann.university) or self.registry.match(raw.title)
            if uni is None:
                print(f"ℹ️ 丢弃: 高校不在名录中 → {ann.university}")
                continue
            ann.university = uni["name"]
            ann.province = uni["province"]
            ann.city = uni["city"]
            if not ann.university_level:
                ann.university_level = uni.get("level", "")
            ann.verified = True
            ann.source = raw.source
            # ⑤ 指纹去重
            ann.id = fingerprint(ann.university, ann.announcement_title, ann.announcement_url, raw.source)
            if ann.id in seen_ids:
                continue
            seen_ids.add(ann.id)
            results.append(ann)

        return results

    # ------------------------------------------------------------------
    # 阶段实现
    # ------------------------------------------------------------------
    def _collect(self, province: str, city: str) -> List[RawAnnouncement]:
        """线程池并发抓取所有源 (复用 MultiSourceJobEngine 的并发模式)."""
        raw_all: List[RawAnnouncement] = []
        if not self.sources:
            return raw_all
        with ThreadPoolExecutor(max_workers=len(self.sources)) as pool:
            futures = {
                pool.submit(source.fetch, province, city, self.registry): source
                for source in self.sources
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    raw_all.extend(future.result())
                except Exception as e:  # noqa: BLE001 — 单源失败不阻塞整体
                    print(f"⚠️ 数据源 [{source.source_name}] 抓取失败: {e}")
        return raw_all

    @staticmethod
    def _prefilter(raw: RawAnnouncement) -> bool:
        if not raw.title or not raw.url:
            return False
        if not raw.url.startswith(("http://", "https://")):
            return False
        # 拒绝模板化假 URL (旧版 D4 缺陷的典型特征)
        if any(p in raw.url for p in ("example.com", "{", "}", " ")):
            return False
        return any(kw in raw.title for kw in COUNSELOR_KEYWORDS)

    def _extract(
        self,
        raw: RawAnnouncement,
        province: str,
        city: str,
        batch_ts: str,
        llm: DeepSeekJobHunter,
    ) -> Optional[UniversityCounselorAnnouncement]:
        # 人工收录源带完整 meta / 无可用 LLM Key: 走无损直接映射
        if raw.meta or llm.client is None:
            return self._direct_map(raw, province, city, batch_ts)
        return self._llm_extract(raw, province, city, batch_ts, llm)

    def _direct_map(
        self, raw: RawAnnouncement, province: str, city: str, batch_ts: str
    ) -> UniversityCounselorAnnouncement:
        """无损直接映射: 只使用原始数据中实际存在的字段, 永不编造."""
        meta = raw.meta or {}
        uni = self.registry.match(meta.get("university") or raw.title)
        prov_clean = province.replace("省", "").replace("市", "").strip() if province not in (None, "all") else ""
        city_clean = city.replace("市", "").strip() if city not in (None, "all") else ""

        return UniversityCounselorAnnouncement(
            id="",
            university=uni["name"] if uni else (meta.get("university") or raw.title),
            university_level=meta.get("university_level", ""),
            province=uni["province"] if uni else (meta.get("province") or prov_clean),
            city=uni["city"] if uni else (meta.get("city") or city_clean),
            has_announcement=bool(meta.get("has_announcement", True)),
            announcement_status=meta.get("announcement_status", "🟢 已发布招聘公告"),
            announcement_title=raw.title,
            publish_date=raw.publish_date or meta.get("publish_date", ""),
            announcement_url=raw.url,
            requirements_summary=meta.get("requirements_summary") or raw.snippet,
            fetched_at=batch_ts,
            source=raw.source,
            verified=uni is not None,
        )

    def _llm_extract(
        self,
        raw: RawAnnouncement,
        province: str,
        city: str,
        batch_ts: str,
        llm: DeepSeekJobHunter,
    ) -> Optional[UniversityCounselorAnnouncement]:
        user_prompt = (
            f"目标地区: {province}·{city}\n"
            f"公告标题: {raw.title}\n"
            f"公告摘要/正文: {(raw.snippet or '')[:2000]}\n"
            f"公告来源链接 (由系统回填，无需处理): {raw.url}"
        )
        try:
            response = llm.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            data = json.loads(response.choices[0].message.content)
            if not data.get("has_announcement", False):
                return None
            return UniversityCounselorAnnouncement(
                id="",
                university=data.get("university", "") or raw.title,
                university_level=data.get("university_level", ""),
                province="",
                city="",
                has_announcement=True,
                announcement_status="🟢 已发布招聘公告",
                announcement_title=data.get("announcement_title") or raw.title,
                publish_date=data.get("publish_date", ""),
                announcement_url=raw.url,  # URL 只来自原始抓取, 永不采用 LLM 产出
                requirements_summary=data.get("requirements_summary", ""),
                fetched_at=batch_ts,
                source=raw.source,
                verified=False,
            )
        except Exception as e:  # noqa: BLE001 — LLM 失败降级为直接映射
            print(f"⚠️ LLM 提取异常, 降级直接映射: {e}")
            return self._direct_map(raw, province, city, batch_ts)
