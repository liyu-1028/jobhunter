"""岗位多源聚合器 — 并发抓取 + 五层校验管线 (镜像辅导员引擎 CounselorAggregator).

校验管线 (逐层丢弃脏数据):
① 预过滤 (URL 合法性) + 关键词重叠粗评分, 截取 Top N 控制下游成本;
② LLM 批量结构化提取 + 匹配度评分 (提取与评分合并为同一调用, 批次 5 条、
   每次搜索总调用封顶, 无 LLM Key 时降级启发式直接映射);
③ URL 溯源: 岗位链接必须等于原始抓取链接 (LLM 永不产出 URL);
④ 来源与校验标记回填;
⑤ 增强指纹去重 (公司|岗位|归一化URL|来源).
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from src.models import UserProfile, JobItem
from src.deepseek_client import DeepSeekJobHunter
from src.adapters.job_base import BaseJobSource, RawJob, job_fingerprint
from src.adapters.query_expander import QueryExpander

# 提取 + 评分合并 Prompt (不要求输出 URL, 链接由系统回填)
_LLM_SYSTEM_PROMPT = """你是一个招聘岗位结构化提取与匹配度评分专家。
输入是一批编号的候选岗位信息。请对每一条判断是否为真实招聘岗位/招聘公告，若是则提取字段并根据求职者背景评估匹配度。
严格输出 JSON（不要包裹 markdown 代码块）：
{
  "jobs": [
    {
      "index": 0,
      "is_job_posting": true,
      "company": "公司官方全称",
      "title": "岗位名称",
      "location": "工作城市(无法确定时输出空字符串)",
      "salary": "薪资范围(无法确定时输出空字符串)",
      "company_type": "公司性质(互联网大厂/国企/外企/独角兽等)",
      "requirements": ["要求1", "要求2"],
      "description": "岗位描述简述(50字内)",
      "match_score": 0-100的整数,
      "recommend_reason": "结合求职者背景的推荐理由(50字内)"
    }
  ]
}
规则：
1. index 字段必须与输入编号对应；不要输出任何 URL / 链接字段，链接由系统统一回填；
2. 如果某条不是招聘岗位(新闻资讯、培训课程、广告等)，对该条只输出 {"index": n, "is_job_posting": false}；
3. 只提取文本中明确出现的信息，不要推测或编造公司名、薪资。"""


class JobAggregator:
    """多源聚合器: 替代旧版 MultiSourceJobEngine 的抓取+直出模式."""

    MAX_AFTER_PREFILTER = 30   # ① 预过滤后截取上限
    LLM_BATCH_SIZE = 5         # ② 每次 LLM 调用处理条数
    MAX_LLM_CALLS = 8          # ② 每次搜索 LLM 调用封顶 (成本控制)

    def __init__(self, sources: List[BaseJobSource], api_key: Optional[str] = None):
        self.sources = sources
        self.api_key = api_key

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def run(self, profile: UserProfile, batch_timestamp: str = None) -> List[JobItem]:
        batch_timestamp = batch_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        queries = QueryExpander().expand(profile)
        raw_all = self._collect(queries, profile)

        # ① 预过滤 + 关键词重叠粗评分 + Top N 截取
        keywords = [k.strip() for k in (profile.keywords or "").split(",") if k.strip()]
        candidates: List[Tuple[RawJob, int]] = []
        for raw in raw_all:
            if not self._prefilter(raw):
                continue
            candidates.append((raw, self._keyword_overlap(raw, keywords)))
        candidates.sort(key=lambda pair: pair[1], reverse=True)
        candidates = candidates[: self.MAX_AFTER_PREFILTER]

        llm = DeepSeekJobHunter(api_key=self.api_key)
        results: List[JobItem] = []
        seen_ids = set()
        llm_calls = 0

        for start in range(0, len(candidates), self.LLM_BATCH_SIZE):
            batch = candidates[start: start + self.LLM_BATCH_SIZE]

            # ② 结构化提取 + 匹配度评分
            if llm.client is not None and llm_calls < self.MAX_LLM_CALLS:
                jobs = self._llm_extract_batch(batch, profile, batch_timestamp, llm)
                llm_calls += 1
            else:
                jobs = [
                    self._direct_map(raw, overlap, profile, batch_timestamp)
                    for raw, overlap in batch
                ]

            for job, (raw, _overlap) in zip(jobs, batch):
                if job is None:
                    continue
                # ③ URL 溯源: 链接只能来自原始抓取结果
                if job.apply_url != raw.url:
                    print(f"ℹ️ 丢弃: URL 不可溯源 → {job.apply_url}")
                    continue
                # ④ 来源与校验标记回填
                job.source = raw.source
                job.verified = True
                job.fetched_at = batch_timestamp
                # ⑤ 增强指纹去重
                job.id = job_fingerprint(job.company, job.title, raw.url, raw.source)
                if job.id in seen_ids:
                    continue
                seen_ids.add(job.id)
                results.append(job)

        # 按匹配度降序排列
        results.sort(key=lambda j: j.match_score, reverse=True)
        return results

    # ------------------------------------------------------------------
    # 阶段实现
    # ------------------------------------------------------------------
    def _collect(self, queries: List[str], profile: UserProfile) -> List[RawJob]:
        """线程池并发抓取所有可用源 (复用 MultiSourceJobEngine 的并发模式)."""
        available = [s for s in self.sources if s.available]
        raw_all: List[RawJob] = []
        if not available:
            print("⚠️ 无可用岗位数据源 (请检查 SERPER_API_KEY / TAVILY_API_KEY 配置)")
            return raw_all

        with ThreadPoolExecutor(max_workers=len(available)) as pool:
            futures = {
                pool.submit(source.fetch, queries, profile): source
                for source in available
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    raw_all.extend(future.result())
                except Exception as e:  # noqa: BLE001 — 单源失败不阻塞整体
                    print(f"⚠️ 数据源 [{source.source_name}] 抓取失败: {e}")
        return raw_all

    @staticmethod
    def _prefilter(raw: RawJob) -> bool:
        if not raw.title or not raw.url:
            return False
        if not raw.url.startswith(("http://", "https://")):
            return False
        # 拒绝模板化假 URL (旧版造假数据的典型特征)
        if any(p in raw.url for p in ("example.com", "{", "}", " ")):
            return False
        # 拒绝含非 ASCII 字符的 URL: 如旧版编造的 "rsc.芜湖.edu.cn" 式中文域名;
        # 合法搜索结果一律返回 ASCII 域名 (国际化域名以 punycode 编码)
        if not raw.url.isascii():
            return False
        return True

    @staticmethod
    def _keyword_overlap(raw: RawJob, keywords: List[str]) -> int:
        """用户关键词在标题/摘要/公司中的命中数 (粗排序依据)."""
        if not keywords:
            return 0
        text = f"{raw.title} {raw.snippet} {raw.company}"
        return sum(1 for kw in keywords if kw in text)

    @staticmethod
    def _company_from_url(url: str) -> str:
        """无公司名时以来源域名兜底标识 (诚实标注, 不编造公司名)."""
        try:
            netloc = urlparse(url).netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc or "未知公司"
        except Exception:  # noqa: BLE001
            return "未知公司"

    def _direct_map(
        self, raw: RawJob, overlap: int, profile: UserProfile, batch_ts: str
    ) -> JobItem:
        """启发式直接映射: 只使用原始数据中实际存在的字段, 永不编造."""
        hit_kws = [
            kw for kw in (profile.keywords or "").split(",")
            if kw.strip() and kw.strip() in f"{raw.title} {raw.snippet} {raw.company}"
        ]
        score = min(60 + overlap * 12, 95) if overlap else 55
        reason = (
            f"关键词命中: {'、'.join(hit_kws)}（启发式匹配，未启用 LLM 评估）"
            if hit_kws
            else f"{raw.source} 搜索结果（启发式匹配，未启用 LLM 评估）"
        )
        return JobItem(
            id="",
            title=raw.title,
            company=raw.company or self._company_from_url(raw.url),
            company_type="",
            company_size="",
            location=raw.location,
            salary=raw.salary or "面议",
            batch=profile.batch,
            match_score=score,
            recommend_reason=reason,
            requirements=[],
            tags=[],
            apply_url=raw.url,
            source=raw.source,
            fetched_at=batch_ts,
            description=(raw.snippet or "")[:300],
            publish_date=raw.publish_date,
            verified=False,
        )

    def _llm_extract_batch(
        self,
        batch: List[Tuple[RawJob, int]],
        profile: UserProfile,
        batch_ts: str,
        llm: DeepSeekJobHunter,
    ) -> List[Optional[JobItem]]:
        """LLM 批量提取 + 评分; 失败时整批降级启发式映射."""
        lines = []
        for i, (raw, _overlap) in enumerate(batch):
            lines.append(f"[{i}] 标题: {raw.title}\n    摘要: {(raw.snippet or '')[:300]}")

        user_prompt = f"""求职者背景:
- 学历: {profile.degree} / 院校: {profile.school} / 专业: {profile.major}
- 招聘批次: {profile.batch} / 目标行业: {profile.target_industry}
- 期望公司性质: {profile.company_type} / 期望城市: {profile.location}
- 岗位关键词: {profile.keywords}

候选岗位列表:
{chr(10).join(lines)}

请按编号顺序输出 JSON。"""

        jobs: List[Optional[JobItem]] = [None] * len(batch)
        try:
            response = llm.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            items = {
                item.get("index"): item
                for item in data.get("jobs", [])
                if isinstance(item, dict)
            }
        except Exception as e:  # noqa: BLE001 — 整批降级
            print(f"⚠️ LLM 批量提取失败, 降级启发式映射: {e}")
            return [
                self._direct_map(raw, overlap, profile, batch_ts)
                for raw, overlap in batch
            ]

        for i, (raw, overlap) in enumerate(batch):
            item = items.get(i)
            if not item or not item.get("is_job_posting", False):
                continue  # 非招聘内容 → 丢弃
            try:
                score = int(item.get("match_score", 75))
            except (TypeError, ValueError):
                score = 75
            jobs[i] = JobItem(
                id="",
                title=item.get("title") or raw.title,
                company=item.get("company") or raw.company or self._company_from_url(raw.url),
                company_type=item.get("company_type", ""),
                company_size="",
                location=item.get("location") or raw.location,
                salary=item.get("salary") or raw.salary or "面议",
                batch=profile.batch,
                match_score=max(0, min(100, score)),
                recommend_reason=item.get("recommend_reason") or "LLM 智能匹配",
                requirements=item.get("requirements") or [],
                tags=[],
                apply_url=raw.url,  # URL 只来自原始抓取, 永不采用 LLM 产出
                source=raw.source,
                fetched_at=batch_ts,
                description=(item.get("description") or raw.snippet or "")[:300],
                publish_date=raw.publish_date,
                verified=False,
            )
        return jobs
