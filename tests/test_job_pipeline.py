"""岗位搜索引擎重构管线测试.

覆盖: 增强指纹、QueryExpander 多维展开、预过滤、"假 URL 零入库"不变量、
URL 溯源与指纹去重离线端到端、Facade/工厂兼容性. 全部离线路径, 不依赖网络.
"""

import pytest

from src.engine import create_default_engine
from src.models import UserProfile
from src.adapters.job_base import RawJob, job_fingerprint
from src.adapters.job_aggregator import JobAggregator
from src.adapters.job_search_adapter import JobSearchAdapter
from src.adapters.query_expander import QueryExpander


@pytest.fixture
def profile():
    return UserProfile(
        degree="硕士",
        school="浙江大学",
        major="计算机",
        batch="2026届秋招",
        target_industry="互联网",
        company_type="大厂/国企",
        company_size="1000人以上",
        location="杭州",
        keywords="Python, 大模型",
    )


# ----------------------------------------------------------------------
# 增强指纹
# ----------------------------------------------------------------------
def test_job_fingerprint_normalization():
    fp1 = job_fingerprint("腾讯", "Python开发", "https://join.qq.com/job/1?track=x", "serper")
    fp2 = job_fingerprint("腾讯", "Python开发", "http://join.qq.com/job/1", "serper")
    assert fp1 == fp2  # 协议/追踪参数差异不影响指纹
    assert fp1.startswith("job_") and len(fp1) == 4 + 16

    fp3 = job_fingerprint("腾讯", "Python开发", "https://join.qq.com/job/2", "serper")
    assert fp3 != fp1  # 不同 URL 必须区分


# ----------------------------------------------------------------------
# QueryExpander 多维展开
# ----------------------------------------------------------------------
def test_query_expander_strategies(profile):
    queries = QueryExpander().expand(profile)
    assert 0 < len(queries) <= QueryExpander.MAX_QUERIES
    # 策略覆盖: 关键词×城市精准 query / site: 大厂定向 / 学校内推
    assert any("Python" in q and "杭州" in q for q in queries)
    assert any(q.startswith("site:") for q in queries)
    assert any("浙江大学" in q for q in queries)
    # 已去重
    assert len(queries) == len(set(queries))


# ----------------------------------------------------------------------
# 预过滤
# ----------------------------------------------------------------------
def test_prefilter_rejects_fake_urls():
    assert JobAggregator._prefilter(RawJob(title="Python开发", url="https://hr.testcorp.cn/job/1"))
    # 模板化假 URL (旧版造假数据的典型特征)
    assert not JobAggregator._prefilter(RawJob(title="Python开发", url="https://rsc.{city}.edu.cn"))
    assert not JobAggregator._prefilter(RawJob(title="Python开发", url="https://jobs.example.com/1"))
    # 非法 URL / 空标题
    assert not JobAggregator._prefilter(RawJob(title="Python开发", url="not-a-url"))
    assert not JobAggregator._prefilter(RawJob(title="", url="https://hr.testcorp.cn"))


# ----------------------------------------------------------------------
# 核心不变量: 假 URL 零入库
# ----------------------------------------------------------------------
class _FakeJobSource:
    """模拟旧版造假兜底会产出的脏数据."""

    max_queries = 8

    @property
    def source_name(self):
        return "fake"

    @property
    def available(self):
        return True

    def fetch(self, queries, profile=None):
        return [
            RawJob(title="某公司2026年度 Python 大模型工程师招聘",
                   url="https://rsc.芜湖.edu.cn/info/job", source="fake"),
            RawJob(title="Python开发工程师招聘", url="not-a-url", source="fake"),
            RawJob(title="Python 大模型算法工程师",
                   url="https://jobs.example.com/1", source="fake"),
        ]


def test_no_fake_url_invariant(monkeypatch, profile):
    """任何模板假 URL / 非法 URL 都不得出现在聚合结果中."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    agg = JobAggregator(sources=[_FakeJobSource()], api_key=None)
    results = agg.run(profile, batch_timestamp="2026-07-29 10:00:00")
    assert results == []


# ----------------------------------------------------------------------
# URL 溯源 + 指纹去重 离线端到端
# ----------------------------------------------------------------------
class _StubJobSource:
    """结构化 Stub 源: 产出合法 RawJob, 含一条重复链接(追踪参数不同)."""

    max_queries = 8

    @property
    def source_name(self):
        return "stub"

    @property
    def available(self):
        return True

    def fetch(self, queries, profile=None):
        return [
            RawJob(
                title="阿里云 Python 平台研发工程师 2026届秋招",
                url="https://talent.alibaba.com/offers/1001",
                snippet="负责云原生平台研发，要求熟练掌握 Python，有大模型应用开发经验，工作地杭州。",
                company="阿里巴巴集团",
                publish_date="2026-07-20",
                source="stub",
            ),
            RawJob(
                title="字节跳动大模型推理优化工程师",
                url="https://jobs.bytedance.com/campus/position/2002",
                snippet="大模型推理加速方向，精通 Python/C++，杭州/北京。",
                company="字节跳动",
                source="stub",
            ),
            # 与第一条同一链接(仅追踪参数不同) → 归一化指纹去重
            RawJob(
                title="阿里云 Python 平台研发工程师 2026届秋招",
                url="https://talent.alibaba.com/offers/1001?utm_source=feed",
                snippet="同上一条公告",
                company="阿里巴巴集团",
                source="stub",
            ),
        ]


def test_offline_end_to_end_traceability_and_dedup(monkeypatch, profile):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    agg = JobAggregator(sources=[_StubJobSource()], api_key=None)
    jobs = agg.run(profile, batch_timestamp="2026-07-29 10:00:00")

    # 三条原始数据 → 去重后两条
    assert len(jobs) == 2

    stub_urls = {
        "https://talent.alibaba.com/offers/1001",
        "https://jobs.bytedance.com/campus/position/2002",
    }
    for job in jobs:
        # URL 溯源: 必须来自原始抓取集合
        assert job.apply_url in stub_urls
        assert job.verified is True
        assert job.source == "stub"
        assert job.id.startswith("job_")
        assert 0 <= job.match_score <= 100
        assert job.fetched_at == "2026-07-29 10:00:00"

    # 按匹配度降序
    scores = [j.match_score for j in jobs]
    assert scores == sorted(scores, reverse=True)


# ----------------------------------------------------------------------
# 工厂与 Facade 兼容性
# ----------------------------------------------------------------------
def test_factory_and_facade_compat():
    engine = create_default_engine()
    assert isinstance(engine, JobSearchAdapter)
    assert callable(engine.search_all_sources)
    # server.py 的自定义 Key 流程: create_default_engine(api_key=...) 不报错
    engine_with_key = create_default_engine(api_key="sk-test-placeholder")
    assert isinstance(engine_with_key, JobSearchAdapter)
