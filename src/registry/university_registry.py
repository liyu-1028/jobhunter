"""高校名录注册表 — 辅导员查询引擎的主数据组件.

加载优先级:
1. data/moe_universities.json 快照 (由 scripts/import_moe_list.py 从教育部
   《全国普通高等学校名单》Excel 生成, 覆盖全国 3100+ 所高校)
2. 内置种子名录 SEED_UNIVERSITIES (少量真实高校, 保证无名录文件时核心可用)

两种来源会合并, 种子名录补充快照中缺失的条目.
"""

import os
import sys
import json
import difflib
from typing import Dict, List, Optional

if getattr(sys, "frozen", False):
    PROJECT_ROOT = sys._MEIPASS
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DEFAULT_REGISTRY_JSON = os.path.join(PROJECT_ROOT, "data", "moe_universities.json")

# 种子名录: 真实存在的高校 (省份/城市为公认事实).
# 完整名录请运行 scripts/import_moe_list.py 导入教育部名单生成.
SEED_UNIVERSITIES: List[Dict] = [
    # 安徽省
    {"name": "中国科学技术大学", "province": "安徽", "city": "合肥", "level": "985/双一流", "ownership": "公办"},
    {"name": "合肥工业大学", "province": "安徽", "city": "合肥", "level": "211/双一流", "ownership": "公办"},
    {"name": "安徽大学", "province": "安徽", "city": "合肥", "level": "211/双一流", "ownership": "公办"},
    {"name": "安徽师范大学", "province": "安徽", "city": "芜湖", "level": "省属重点公办", "ownership": "公办"},
    {"name": "安徽工程大学", "province": "安徽", "city": "芜湖", "level": "省属重点公办", "ownership": "公办"},
    {"name": "皖南医学院", "province": "安徽", "city": "芜湖", "level": "省属医科高校", "ownership": "公办"},
    {"name": "芜湖职业技术学院", "province": "安徽", "city": "芜湖", "level": "双高计划高职", "ownership": "公办"},
    {"name": "安徽商贸职业技术学院", "province": "安徽", "city": "芜湖", "level": "省属公办高职", "ownership": "公办"},
    # 北京市
    {"name": "北京大学", "province": "北京", "city": "北京", "level": "985/双一流", "ownership": "公办"},
    {"name": "清华大学", "province": "北京", "city": "北京", "level": "985/双一流", "ownership": "公办"},
    {"name": "北京师范大学", "province": "北京", "city": "北京", "level": "985/双一流", "ownership": "公办"},
    {"name": "中国人民大学", "province": "北京", "city": "北京", "level": "985/双一流", "ownership": "公办"},
    # 上海市
    {"name": "复旦大学", "province": "上海", "city": "上海", "level": "985/双一流", "ownership": "公办"},
    {"name": "上海交通大学", "province": "上海", "city": "上海", "level": "985/双一流", "ownership": "公办"},
    {"name": "同济大学", "province": "上海", "city": "上海", "level": "985/双一流", "ownership": "公办"},
    {"name": "华东师范大学", "province": "上海", "city": "上海", "level": "985/双一流", "ownership": "公办"},
    # 浙江省
    {"name": "浙江大学", "province": "浙江", "city": "杭州", "level": "985/双一流", "ownership": "公办"},
    {"name": "浙江工业大学", "province": "浙江", "city": "杭州", "level": "省属重点公办", "ownership": "公办"},
    {"name": "杭州电子科技大学", "province": "浙江", "city": "杭州", "level": "省属重点公办", "ownership": "公办"},
    {"name": "宁波大学", "province": "浙江", "city": "宁波", "level": "双一流", "ownership": "公办"},
    # 江苏省
    {"name": "南京大学", "province": "江苏", "city": "南京", "level": "985/双一流", "ownership": "公办"},
    {"name": "东南大学", "province": "江苏", "city": "南京", "level": "985/双一流", "ownership": "公办"},
    {"name": "南京师范大学", "province": "江苏", "city": "南京", "level": "211/双一流", "ownership": "公办"},
    {"name": "苏州大学", "province": "江苏", "city": "苏州", "level": "211/双一流", "ownership": "公办"},
    # 湖北省
    {"name": "武汉大学", "province": "湖北", "city": "武汉", "level": "985/双一流", "ownership": "公办"},
    {"name": "华中科技大学", "province": "湖北", "city": "武汉", "level": "985/双一流", "ownership": "公办"},
    {"name": "华中师范大学", "province": "湖北", "city": "武汉", "level": "211/双一流", "ownership": "公办"},
    # 湖南省
    {"name": "中南大学", "province": "湖南", "city": "长沙", "level": "985/双一流", "ownership": "公办"},
    {"name": "湖南大学", "province": "湖南", "city": "长沙", "level": "985/双一流", "ownership": "公办"},
    # 广东省
    {"name": "中山大学", "province": "广东", "city": "广州", "level": "985/双一流", "ownership": "公办"},
    {"name": "华南理工大学", "province": "广东", "city": "广州", "level": "985/双一流", "ownership": "公办"},
    {"name": "深圳大学", "province": "广东", "city": "深圳", "level": "省属重点公办", "ownership": "公办"},
    # 四川省
    {"name": "四川大学", "province": "四川", "city": "成都", "level": "985/双一流", "ownership": "公办"},
    {"name": "电子科技大学", "province": "四川", "city": "成都", "level": "985/双一流", "ownership": "公办"},
    # 陕西省
    {"name": "西安交通大学", "province": "陕西", "city": "西安", "level": "985/双一流", "ownership": "公办"},
]

_NAME_SUFFIXES = ("大学", "学院")


def normalize_region(name: str) -> str:
    """归一化省市名: '芜湖市' → '芜湖', '安徽省' → '安徽'"""
    return (name or "").replace("省", "").replace("市", "").strip()


def _strip_name_suffix(name: str) -> str:
    for suffix in _NAME_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            return name[: -len(suffix)]
    return name


class UniversityRegistry:
    """高校名录只读注册表: 提供 省/市→高校 索引与多级模糊匹配."""

    def __init__(self, entries: List[Dict]):
        self._entries = entries
        self._by_name: Dict[str, Dict] = {}
        for entry in entries:
            norm = normalize_region(entry.get("name", "")).strip()
            if norm and norm not in self._by_name:
                record = dict(entry)
                record["name"] = norm
                record["province"] = normalize_region(entry.get("province", ""))
                record["city"] = normalize_region(entry.get("city", ""))
                self._by_name[norm] = record
        # 按名称长度降序: 标题内包含匹配时优先最长校名
        self._names_desc = sorted(self._by_name.keys(), key=len, reverse=True)

    @classmethod
    def load(cls, json_path: str = None) -> "UniversityRegistry":
        path = json_path or DEFAULT_REGISTRY_JSON
        entries: List[Dict] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    entries = [e for e in loaded if isinstance(e, dict) and e.get("name")]
            except (OSError, json.JSONDecodeError) as e:
                print(f"⚠️ 高校名录快照加载失败, 回退种子名录: {e}")
        else:
            print(
                f"ℹ️ 未找到高校名录快照 ({path}), 使用内置种子名录 "
                f"({len(SEED_UNIVERSITIES)} 所)。"
                "运行 scripts/import_moe_list.py 可导入教育部完整名录 (3100+ 所)"
            )

        seen = {normalize_region(e.get("name", "")) for e in entries}
        for seed in SEED_UNIVERSITIES:
            if normalize_region(seed["name"]) not in seen:
                entries.append(seed)
                seen.add(normalize_region(seed["name"]))
        return cls(entries)

    def __len__(self) -> int:
        return len(self._by_name)

    def list_by(self, province: str = "all", city: str = "all") -> List[Dict]:
        """按省/市筛选高校列表 (动态替代旧版手写 CITY_UNIVERSITY_MAP)."""
        prov = normalize_region(province) if province not in (None, "all") else ""
        c = normalize_region(city) if city not in (None, "all") else ""
        result = []
        for entry in self._by_name.values():
            if prov and entry["province"] != prov:
                continue
            if c and entry["city"] != c:
                continue
            result.append(entry)
        return result

    def match(self, text: str) -> Optional[Dict]:
        """多级匹配: 精确 → 标题包含 → 去后缀相等 → 模糊相似度 (≥0.86)."""
        if not text:
            return None
        t = normalize_region(text).strip()
        if not t:
            return None

        if t in self._by_name:
            return self._by_name[t]

        for name in self._names_desc:
            if name in t:
                return self._by_name[name]

        t_core = _strip_name_suffix(t)
        for name, record in self._by_name.items():
            if _strip_name_suffix(name) == t_core:
                return record

        best, best_ratio = None, 0.0
        for name, record in self._by_name.items():
            ratio = difflib.SequenceMatcher(None, t, name).ratio()
            if ratio > best_ratio:
                best, best_ratio = record, ratio
        return best if best_ratio >= 0.86 else None

    def exists(self, text: str) -> bool:
        return self.match(text) is not None
