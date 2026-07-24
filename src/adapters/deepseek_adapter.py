from typing import List
from src.models import UserProfile, JobItem
from src.adapters.base import BaseJobSourceAdapter
from src.deepseek_client import DeepSeekJobHunter


class DeepSeekAdapter(BaseJobSourceAdapter):
    """DeepSeek 大模型 AI 岗位匹配引擎适配器"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.hunter = DeepSeekJobHunter(api_key=api_key, base_url=base_url)

    @property
    def source_name(self) -> str:
        return "DeepSeek"

    def fetch_jobs(self, profile: UserProfile) -> List[JobItem]:
        result = self.hunter.search_jobs(profile, mock_if_no_key=True)
        return result.jobs
