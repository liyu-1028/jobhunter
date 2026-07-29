from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from src.models import UserProfile, JobItem, SearchResult
from src.adapters.base import BaseJobSourceAdapter
from src.adapters.deepseek_adapter import DeepSeekAdapter
from src.adapters.nowcoder import NowcoderAdapter
from src.adapters.haitou import HaitouAdapter
from src.adapters.job_search_adapter import JobSearchAdapter


class MultiSourceJobEngine:
    """多数据源岗位聚合与去重引擎"""

    def __init__(self, adapters: List[BaseJobSourceAdapter] = None):
        self.adapters: List[BaseJobSourceAdapter] = adapters or []

    def register_adapter(self, adapter: BaseJobSourceAdapter):
        """注册新的岗位数据源适配器"""
        self.adapters.append(adapter)

    def search_all_sources(self, profile: UserProfile) -> SearchResult:
        """并发并行调用所有注册的数据源，聚合并按 MD5 指纹去重"""
        all_raw_jobs: List[JobItem] = []

        # 使用线程池并发抓取多数据源
        with ThreadPoolExecutor(max_workers=len(self.adapters) or 1) as executor:
            future_to_adapter = {
                executor.submit(adapter.fetch_jobs, profile): adapter 
                for adapter in self.adapters
            }
            
            for future in as_completed(future_to_adapter):
                adapter = future_to_adapter[future]
                try:
                    jobs = future.result()
                    all_raw_jobs.extend(jobs)
                except Exception as e:
                    print(f"⚠️ 从数据源 [{adapter.source_name}] 拉取数据失败: {e}")

        # 指纹无感去重与数据合并
        seen_fingerprints = set()
        unique_jobs: List[JobItem] = []

        # 使用任意一个 adapter 辅助计算指纹
        helper_adapter = self.adapters[0] if self.adapters else DeepSeekAdapter()

        for job in all_raw_jobs:
            fp = helper_adapter.generate_fingerprint(job)
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                unique_jobs.append(job)

        # 按匹配度降序排列
        unique_jobs.sort(key=lambda x: x.match_score, reverse=True)

        return SearchResult(
            search_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_found=len(unique_jobs),
            jobs=unique_jobs
        )


def create_default_engine(api_key: str = None) -> JobSearchAdapter:
    """创建默认岗位搜索引擎 (Serper/Tavily 多源真实搜索 + 五层校验管线).

    返回的 JobSearchAdapter 与旧版 MultiSourceJobEngine 方法签名一致
    (search_all_sources(profile) -> SearchResult), 调用方零改动。
    旧版 MultiSourceJobEngine 与假数据适配器保留至 P1 阶段统一删除。
    """
    return JobSearchAdapter(api_key=api_key)
