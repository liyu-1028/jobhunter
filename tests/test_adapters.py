import pytest
from src.models import UserProfile, JobItem
from src.adapters.base import BaseJobSourceAdapter


class MockAdapter(BaseJobSourceAdapter):
    @property
    def source_name(self) -> str:
        return "MockSource"

    def fetch_jobs(self, profile: UserProfile) -> list[JobItem]:
        return [
            JobItem(
                id="test-1",
                title="Python开发",
                company="测试公司",
                company_type="民企",
                company_size="100-500人",
                salary="20k-30k",
                location="杭州",
                batch="2026届秋招",
                match_score=90,
                recommend_reason="测试理由",
                requirements=["Python基础"],
                apply_url="https://example.com",
                tags=["Python"]
            )
        ]


def test_base_adapter_fingerprint():
    adapter = MockAdapter()
    job = JobItem(
        id="test-1",
        title="  Python开发  ",
        company=" 测试公司 ",
        company_type="民企",
        company_size="100-500人",
        salary="20k-30k",
        location="杭州 ",
        batch="2026届秋招",
        match_score=90,
        recommend_reason="测试理由",
        requirements=[],
        apply_url="https://example.com",
        tags=[]
    )
    
    fp1 = adapter.generate_fingerprint(job)
    assert isinstance(fp1, str)
    assert len(fp1) == 32  # MD5 hex digest 长度为 32

    # 大小写与首尾空格不敏感测试
    job2 = JobItem(
        id="test-2",
        title="python开发",
        company="测试公司",
        company_type="民企",
        company_size="100-500人",
        salary="20k-30k",
        location="杭州",
        batch="2026届秋招",
        match_score=85,
        recommend_reason="测试理由",
        requirements=[],
        apply_url="https://example.com",
        tags=[]
    )
    fp2 = adapter.generate_fingerprint(job2)
    assert fp1 == fp2  # 相同公司+岗位+城市指纹应该完全一致
