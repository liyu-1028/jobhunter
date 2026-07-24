import hashlib
from abc import ABC, abstractmethod
from typing import List
from src.models import UserProfile, JobItem


class BaseJobSourceAdapter(ABC):
    """多数据源岗位获取抽象基类适配器"""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称标识 (如: DeepSeek, Nowcoder, Haitou)"""
        pass

    @abstractmethod
    def fetch_jobs(self, profile: UserProfile) -> List[JobItem]:
        """根据求职 Profile 检索/抓取岗位列表"""
        pass

    def generate_fingerprint(self, job: JobItem) -> str:
        """生成岗位唯一 MD5 指纹，用于跨数据源无感去重"""
        company = (job.company or "").strip().lower()
        title = (job.title or "").strip().lower()
        location = (job.location or "").strip().lower()
        
        raw_key = f"{company}_{title}_{location}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()
