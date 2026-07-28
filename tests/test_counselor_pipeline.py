"""辅导员查询引擎重构管线测试.

覆盖: 增强指纹、高校名录匹配、预过滤、"假数据零入库"核心不变量、
人工收录源离线端到端、Facade 签名兼容性.
"""

import pytest

from src.adapters.counselor_adapter import CounselorJobAdapter
from src.adapters.counselor_aggregator import CounselorAggregator
from src.adapters.counselor_base import BaseCounselorSource, RawAnnouncement, fingerprint
from src.adapters.counselor_curated import CuratedSource
from src.registry.university_registry import UniversityRegistry


@pytest.fixture(scope="module")
def registry():
    return UniversityRegistry.load()


# ----------------------------------------------------------------------
# 增强指纹
# ----------------------------------------------------------------------
def test_fingerprint_url_normalization():
    fp1 = fingerprint("安徽师范大学", "辅导员招聘", "https://rsc.ahnu.edu.cn/info/1.htm?track=x", "bing")
    fp2 = fingerprint("安徽师范大学", "辅导员招聘", "http://rsc.ahnu.edu.cn/info/1.htm", "bing")
    assert fp1 == fp2  # 协议/追踪参数差异不影响指纹
    assert fp1.startswith("ann_") and len(fp1) == 4 + 16

    fp3 = fingerprint("安徽师范大学", "辅导员招聘", "https://rsc.ahnu.edu.cn/info/2.htm", "bing")
    assert fp3 != fp1  # 不同 URL 必须区分


# ----------------------------------------------------------------------
# 高校名录注册表
# ----------------------------------------------------------------------
def test_registry_match_exact(registry):
    assert registry.match("安徽师范大学")["city"] == "芜湖"

def test_registry_match_in_title(registry):
    uni = registry.match("安徽师范大学2026年专职辅导员公开招聘公告")
    assert uni is not None and uni["name"] == "安徽师范大学"

def test_registry_match_fuzzy(registry):
    assert registry.match("安徽师范大") is not None

def test_registry_match_absent(registry):
    assert registry.match("霍格沃茨魔法学校") is None

def test_registry_list_by_wuhu(registry):
    names = {u["name"] for u in registry.list_by(province="安徽", city="芜湖")}
    assert "安徽师范大学" in names
    assert len(registry.list_by()) >= len(names)


# ----------------------------------------------------------------------
# 预过滤
# ----------------------------------------------------------------------
def test_prefilter_rejects_fake_and_irrelevant(registry):
    agg = CounselorAggregator(sources=[], registry=registry)
    # 无关标题
    assert not agg._prefilter(RawAnnouncement(title="英语培训招生", url="https://x.com"))
    # 模板化假 URL (旧版 D4 缺陷特征)
    assert not agg._prefilter(RawAnnouncement(title="芜湖辅导员招聘", url="https://rsc.{city}.edu.cn"))
    assert not agg._prefilter(RawAnnouncement(title="芜湖辅导员招聘", url="https://rsc.example.com"))
    # 空标题 / 非 http
    assert not agg._prefilter(RawAnnouncement(title="", url="https://x.com"))
    assert not agg._prefilter(RawAnnouncement(title="辅导员招聘", url="not-a-url"))
    # 合法条目
    assert agg._prefilter(RawAnnouncement(title="安徽师范大学专职辅导员招聘", url="https://rsc.ahnu.edu.cn"))


# ----------------------------------------------------------------------
# 核心不变量: 假数据零入库
# ----------------------------------------------------------------------
class _FakeSource(BaseCounselorSource):
    """模拟旧版造假兜底产出的脏数据."""

    @property
    def source_name(self) -> str:
        return "fake"

    def fetch(self, province="all", city="all", registry=None):
        return [
            # 模板化假 URL
            RawAnnouncement(
                title="某高校2026/2027年度专职辅导员公开招聘公告",
                url="https://rsc.芜湖.edu.cn/info/counselor",
                source="fake",
            ),
            # 非法 URL
            RawAnnouncement(title="辅导员招聘", url="not-a-url", source="fake"),
            # 虚构高校 + example 域名
            RawAnnouncement(
                title="霍格沃茨魔法学校辅导员招聘",
                url="https://hogwarts.example.com",
                source="fake",
            ),
        ]


def test_no_fake_data_invariant(monkeypatch, registry):
    """任何编造的 URL / 虚构高校都不得出现在聚合结果中."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    agg = CounselorAggregator(sources=[_FakeSource()], registry=registry, api_key=None)
    results = agg.run(province="all", city="all", batch_timestamp="2026-07-28 10:00:00")
    assert results == []


# ----------------------------------------------------------------------
# 人工收录源离线端到端
# ----------------------------------------------------------------------
def test_curated_end_to_end_offline(monkeypatch, registry):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    agg = CounselorAggregator(sources=[CuratedSource()], registry=registry, api_key=None)
    anns = agg.run(province="安徽", city="芜湖", batch_timestamp="2026-07-28 10:00:00")

    assert len(anns) >= 4
    names = {a.university for a in anns}
    assert {"安徽师范大学", "安徽工程大学", "皖南医学院"} <= names
    for ann in anns:
        assert ann.verified is True
        assert ann.source == "curated"
        assert ann.announcement_url.startswith("http")
        assert ann.city == "芜湖"
        assert ann.id.startswith("ann_")


# ----------------------------------------------------------------------
# Facade 兼容性
# ----------------------------------------------------------------------
def test_facade_signature_compat():
    adapter = CounselorJobAdapter()
    assert callable(adapter.fetch_search_snippets)
    assert callable(adapter.fetch_university_counselor_announcements)
    assert adapter.aggregator is not None
