import pytest
from src.models import UserProfile, JobItem, SearchResult
from src.adapters.base import BaseJobSourceAdapter
from src.adapters.nowcoder import NowcoderAdapter
from src.adapters.haitou import HaitouAdapter
from src.engine import MultiSourceJobEngine


class DuplicateMockAdapter(BaseJobSourceAdapter):
    @property
    def source_name(self) -> str:
        return "DuplicateMock"

    def fetch_jobs(self, profile: UserProfile) -> list[JobItem]:
        return [
            # 故意与 Nowcoder 重名的岗位
            JobItem(
                id="dup-1",
                title="Python 校招管培生/研发岗",
                company="美团",
                company_type="互联网大厂",
                company_size="10000人以上",
                salary="24k-38k·15.5薪",
                location="杭州",
                batch="2026届秋招",
                match_score=95,
                recommend_reason="重复岗位测试",
                requirements=[],
                apply_url="https://zhaopin.meituan.com",
                tags=["重复项"]
            )
        ]


@pytest.fixture
def sample_profile():
    return UserProfile(
        degree="硕士",
        school="浙江大学",
        major="计算机",
        batch="2026届秋招",
        target_industry="互联网",
        company_type="大厂",
        company_size="1000人以上",
        location="杭州",
        keywords="Python, 大模型"
    )


def test_multi_source_engine_deduplication(sample_profile):
    engine = MultiSourceJobEngine()
    engine.register_adapter(NowcoderAdapter())
    engine.register_adapter(HaitouAdapter())
    engine.register_adapter(DuplicateMockAdapter())

    result = engine.search_all_sources(sample_profile)

    assert isinstance(result, SearchResult)
    assert len(result.jobs) > 0

    # 检查美团岗位是否只出现了一次 (根据公司+岗位+城市指纹自动去重)
    meituan_jobs = [j for j in result.jobs if j.company == "美团" and "校招管培生/研发岗" in j.title]
    assert len(meituan_jobs) == 1

    # 检查岗位列表是否按照 match_score 降序排列
    scores = [j.match_score for j in result.jobs]
    assert scores == sorted(scores, reverse=True)
