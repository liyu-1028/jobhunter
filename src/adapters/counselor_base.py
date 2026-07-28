"""辅导员公告数据源统一契约与共用工具.

所有数据源只产出 RawAnnouncement 原始数据, 不产出最终模型 ——
结构化与合法性校验统一由 CounselorAggregator 的校验管线完成,
从结构上杜绝数据源自行编造公告的可能.
"""

import os
import re
import sys
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

if getattr(sys, "frozen", False):
    PROJECT_ROOT = sys._MEIPASS
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 辅导员招聘公告关键词 (预过滤使用)
COUNSELOR_KEYWORDS = ("辅导员", "学生工作", "思政", "班主任")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass
class RawAnnouncement:
    """各数据源返回的统一原始格式 (未经 LLM 提取)."""

    title: str
    url: str                       # 必须是源实际抓到的链接, 禁止源自行拼接/推测
    snippet: str = ""              # 摘要或正文片段, 供 LLM 提取
    publish_date: str = ""
    source: str = ""               # bing / Gaoxiaojob / uni_hr / curated
    meta: Dict = field(default_factory=dict)  # 人工收录等结构化源的附加字段


class BaseCounselorSource(ABC):
    """辅导员公告数据源抽象基类 (参照 BaseJobSourceAdapter 模式)."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称标识"""
        pass

    @abstractmethod
    def fetch(self, province: str, city: str, registry=None) -> List[RawAnnouncement]:
        """按省/市抓取原始公告列表; 任何异常应自行降级为空列表."""
        pass


def fingerprint(university: str, title: str, url: str, source: str) -> str:
    """增强版指纹: 含归一化 URL 与来源, 16 位 hex.

    URL 归一化: 去协议前缀 / 尾部斜杠 / 查询参数,
    同一公告不同协议与追踪参数的链接产生相同指纹.
    """
    clean_url = re.sub(r"^https?://", "", (url or "").strip()).rstrip("/").split("?")[0]
    fp = f"{(university or '').strip()}|{(title or '').strip()}|{clean_url}|{(source or '').strip()}"
    return f"ann_{hashlib.md5(fp.encode('utf-8')).hexdigest()[:16]}"


def get_with_retry(
    url: str,
    headers: Optional[Dict] = None,
    timeout: int = 10,
    retries: int = 2,
    backoff: float = 2.0,
) -> Optional[requests.Response]:
    """带指数退避重试的 GET; 4xx 不重试, 全部失败返回 None (绝不抛给调用方)."""
    headers = headers or DEFAULT_HEADERS
    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if 400 <= resp.status_code < 500:
                return None
            last_error = f"HTTP {resp.status_code}"
        except Exception as e:  # noqa: BLE001 — 抓取源必须吞掉所有异常
            last_error = str(e)
        if attempt < retries:
            time.sleep(backoff ** attempt)
    print(f"⚠️ 请求失败 (已重试 {retries} 次) {url}: {last_error}")
    return None
