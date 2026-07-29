"""岗位数据源统一契约与共用工具 (镜像辅导员引擎 counselor_base.py).

所有岗位数据源只产出 RawJob 原始数据, 不产出最终 JobItem ——
结构化提取、URL 溯源与匹配度评分统一由 JobAggregator 校验管线完成,
从结构上杜绝数据源自行编造岗位的可能.
"""

import re
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

# 复用辅导员引擎的请求卫生工具
from src.adapters.counselor_base import DEFAULT_HEADERS, get_with_retry  # noqa: F401


@dataclass
class RawJob:
    """各数据源返回的统一原始格式 (未经 LLM 提取)."""

    title: str
    url: str                   # 必须是源实际抓到的链接, 禁止源自行拼接/推测
    snippet: str = ""          # 摘要或正文片段, 供 LLM 提取
    company: str = ""          # 源能直接获取的公司名 (结构化源)
    location: str = ""
    salary: str = ""
    publish_date: str = ""
    source: str = ""           # serper / tavily / bigtech / nowcoder / wechat_rss / ...
    meta: Dict = field(default_factory=dict)  # 附加字段 (query 来源等)


class BaseJobSource(ABC):
    """岗位数据源抽象基类 (参照辅导员引擎 BaseCounselorSource 模式)."""

    #: 单次搜索本源最多消耗的 query 数 (成本控制)
    max_queries: int = 8

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称标识"""
        pass

    @abstractmethod
    def fetch(self, queries: List[str], profile=None) -> List[RawJob]:
        """按 query 组抓取原始岗位; 任何异常应自行降级为空列表."""
        pass

    @property
    def available(self) -> bool:
        """源是否可用 (如 API Key 已配置). 不可用时聚合器直接跳过."""
        return True


def post_with_retry(
    url: str,
    json_body: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 10,
    retries: int = 1,
    backoff: float = 2.0,
) -> Optional[requests.Response]:
    """带指数退避重试的 POST; 4xx 不重试, 全部失败返回 None (绝不抛给调用方)."""
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, json=json_body, headers=merged_headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if 400 <= resp.status_code < 500:
                print(f"⚠️ POST {url} 返回 {resp.status_code} (不重试): {resp.text[:200]}")
                return None
            last_error = f"HTTP {resp.status_code}"
        except Exception as e:  # noqa: BLE001 — 抓取源必须吞掉所有异常
            last_error = str(e)
        if attempt < retries:
            time.sleep(backoff ** attempt)
    print(f"⚠️ POST 请求失败 (已重试 {retries} 次) {url}: {last_error}")
    return None


def job_fingerprint(company: str, title: str, url: str, source: str) -> str:
    """增强版指纹: 含归一化 URL 与来源, 16 位 hex (镜像辅导员引擎 fingerprint).

    URL 归一化: 去协议前缀 / 尾部斜杠 / 查询参数,
    同一岗位不同协议与追踪参数的链接产生相同指纹.
    """
    clean_url = re.sub(r"^https?://", "", (url or "").strip()).rstrip("/").split("?")[0]
    fp = f"{(company or '').strip().lower()}|{(title or '').strip().lower()}|{clean_url}|{(source or '').strip()}"
    return f"job_{hashlib.md5(fp.encode('utf-8')).hexdigest()[:16]}"
