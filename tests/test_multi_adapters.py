import pytest
from src.models import UserProfile, JobItem
from src.adapters.deepseek_adapter import DeepSeekAdapter
from src.adapters.nowcoder import NowcoderAdapter
from src.adapters.haitou import HaitouAdapter


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
        keywords="Python, 算法"
    )


def test_deepseek_adapter(sample_profile):
    adapter = DeepSeekAdapter()
    assert adapter.source_name == "DeepSeek"
    jobs = adapter.fetch_jobs(sample_profile)
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert isinstance(jobs[0], JobItem)


def test_nowcoder_adapter(sample_profile):
    adapter = NowcoderAdapter()
    assert adapter.source_name == "牛客网(Nowcoder)"
    jobs = adapter.fetch_jobs(sample_profile)
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert isinstance(jobs[0], JobItem)
    # 标签中应包含牛客数据源标记
    assert any("牛客" in tag for tag in jobs[0].tags) or "Nowcoder" in jobs[0].tags or "牛客" in jobs[0].company_type


def test_haitou_adapter(sample_profile):
    adapter = HaitouAdapter()
    assert adapter.source_name == "海投网(Haitou)"
    jobs = adapter.fetch_jobs(sample_profile)
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert isinstance(jobs[0], JobItem)
