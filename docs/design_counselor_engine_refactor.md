# 高校辅导员招聘查询引擎重构方案

> **日期**: 2026-07-28
> **状态**: 待实施
> **关联文档**: [research_counselor_expansion.md](./research_counselor_expansion.md)(数据源扩展调研报告)
> **涉及模块**: Tab 3「全国高校辅导员招聘直通车」,入口 `src/adapters/counselor_adapter.py`

---

## 1. 背景与目标

当前辅导员查询引擎存在五项已核实缺陷(详见调研报告第 1 节):城市覆盖仅 17/300+(D1)、高校硬编码仅 14 条(D2)、唯一真实通道为脆弱的 Bing HTML 爬取(D3)、**兜底逻辑凭空编造公告标题与假 URL 入库**(D4,致命)、MD5 指纹去重粒度不足(D5)。

本方案的重构目标:

| 目标 | 现状 | 重构后 |
|---|---|---|
| 地域覆盖 | 17 个城市、65 所高校(手写映射) | 300+ 城市、3,100+ 高校(教育部名录驱动) |
| 数据来源 | Bing 搜索单通道 | 多源适配器并发(Bing site: 定向搜索 + 高校人才网 + 高校人事处 + 省人社厅) |
| 数据真实性 | 兜底编造假公告、假 URL | 四层校验管线 + "URL 溯源"不变量,假数据零入库 |
| 可扩展性 | 新增城市/来源需改代码 | 新增来源只需注册适配器;新增城市零代码 |

架构与现有 `MultiSourceJobEngine`(`src/engine.py`)同构——多源并发 + 指纹去重——后续岗位搜索引擎亦可复用本方案的注册表与校验管线。

---

## 2. 目标架构

```
┌────────────────────────────────────────────────────────────┐
│ /api/fetch_counselors   cli.py(入口不变,签名兼容)           │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ CounselorJobAdapter(瘦身为 Facade,保留原方法签名)           │
│   └── CounselorAggregator                                   │
│         ├── [并发] ThreadPoolExecutor 调度各 Source          │
│         │     ├── BingSiteSearchSource   (现有逻辑重构)      │
│         │     ├── GaoxiaojobSource       (P1 新增)          │
│         │     ├── UniversityHRSource     (P2 新增)          │
│         │     └── ProvincialRSTSource    (P2 新增)          │
│         └── [串行] 校验管线                                   │
│               ① 关键词预过滤(辅导员/思政/学生工作)            │
│               ② LLM 结构化提取(URL 只许引用原文,禁止生成)    │
│               ③ URL 溯源校验(提取结果 URL 必须存在于原始输入) │
│               ④ UniversityRegistry 交叉验证高校名            │
│               ⑤ 增强指纹去重(高校|标题|URL|来源)             │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ UniversityRegistry(新增)     JobDatabase(扩展)              │
│  教育部名录 3,100+ 所         + source 列                    │
│  省/市 ↔ 高校动态索引          过期标记(90 天)               │
│  替代 CITY_UNIVERSITY_MAP     JSON 导出                     │
└────────────────────────────────────────────────────────────┘
```

目录结构变化:

```
src/
├── registry/
│   ├── __init__.py
│   └── university_registry.py     # 新增:高校名录主数据 + 模糊匹配
├── adapters/
│   ├── counselor_base.py          # 新增:RawAnnouncement + BaseCounselorSource
│   ├── counselor_aggregator.py    # 新增:并发调度 + 校验管线
│   ├── counselor_bing.py          # 新增:从 counselor_adapter.py 拆出 Bing 逻辑
│   ├── counselor_gaoxiaojob.py    # 新增(P1):高校人才网源
│   ├── counselor_uni_hr.py        # 新增(P2):高校人事处源
│   ├── counselor_provincial.py    # 新增(P2):省人社厅源
│   └── counselor_adapter.py       # 改造:瘦身为 Facade,签名不变
├── models.py                      # 改造:UniversityCounselorAnnouncement + source 字段
└── db.py                          # 改造:source 列迁移 + 过期标记
data/
└── moe_universities.json          # 新增:教育部名录快照(随仓库分发,年度更新)
scripts/
└── import_moe_list.py             # 新增:Excel → SQLite/JSON 的离线导入脚本
```

---

## 3. 详细设计

### 3.1 Facade 兼容:入口零改动

`server.py` 第 162-167 行与 `cli.py` 第 63-76 行均通过 `CounselorJobAdapter.fetch_university_counselor_announcements(...)` 调用。重构保留该类名与方法签名,内部委托聚合器:

```python
# src/adapters/counselor_adapter.py(重构后)
class CounselorJobAdapter:
    """兼容旧接口的 Facade。server.py / cli.py 无需任何改动。"""

    def __init__(self, api_key: Optional[str] = None):
        self.aggregator = CounselorAggregator(
            sources=[BingSiteSearchSource(), GaoxiaojobSource()],
            registry=UniversityRegistry.load(),
            api_key=api_key,
        )

    def fetch_university_counselor_announcements(
        self,
        province: str = "all",
        city: str = "all",
        batch_timestamp: str = None,
        api_key: Optional[str] = None,
    ) -> List[UniversityCounselorAnnouncement]:
        return self.aggregator.run(
            province=province,
            city=city,
            batch_timestamp=batch_timestamp,
            api_key=api_key,
        )
```

### 3.2 数据源统一契约

所有源**只产出原始数据**,不产出最终模型——从结构上杜绝"源自己编造结构化数据"的可能(这正是 D4 的根因):

```python
# src/adapters/counselor_base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

@dataclass
class RawAnnouncement:
    """各数据源返回的统一原始格式 —— 未经 LLM 提取的原始抓取结果"""
    title: str
    url: str                 # 必须是源实际抓到的链接,不得由源自行拼接/推测
    snippet: str = ""        # 摘要或正文片段,供 LLM 提取
    publish_date: str = ""
    source: str = ""         # "bing" / "gaoxiaojob" / "uni_hr" / "provincial_rst"

class BaseCounselorSource(ABC):
    """辅导员公告数据源抽象基类(参照 BaseJobSourceAdapter 的模式)"""

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def fetch(self, province: str, city: str,
              registry: "UniversityRegistry") -> List[RawAnnouncement]: ...

    # 各源共用的请求卫生配置
    request_timeout: int = 10
    min_interval_seconds: float = 1.5
    max_retries: int = 2
```

`registry` 作为参数传入是关键设计:源可以用它把"省份/城市 → 具体高校"展开为精准 query。例如 `BingSiteSearchSource` 针对芜湖会生成:

```
site:rsc.ahnu.edu.cn 辅导员 招聘
site:rsc.ahpu.edu.cn 辅导员 招聘
安徽 芜湖 高校 辅导员 招聘 公告
```

**query 由名录驱动而非手写映射表**,这是覆盖面从 17 城扩展到全国的核心机制。

### 3.3 校验管线:四层漏斗

聚合器串行执行校验,每层都可独立丢弃脏数据:

```python
# src/adapters/counselor_aggregator.py(核心骨架)
class CounselorAggregator:

    def __init__(self, sources, registry, api_key=None):
        self.sources = sources
        self.registry = registry
        self.api_key = api_key

    def run(self, province, city, batch_timestamp=None, api_key=None):
        batch_timestamp = batch_timestamp or _now()

        # ① 并发抓取所有源(复用 engine.py 的线程池模式)
        raw_all: List[RawAnnouncement] = []
        with ThreadPoolExecutor(max_workers=len(self.sources) or 1) as pool:
            futures = {
                pool.submit(s.fetch, province, city, self.registry): s
                for s in self.sources
            }
            for fut in as_completed(futures):
                src = futures[fut]
                try:
                    raw_all.extend(fut.result())
                except Exception as e:
                    logger.warning("源 [%s] 抓取失败: %s", src.source_name, e)

        results, seen = [], set()
        for raw in raw_all:
            # ② 预过滤:关键词 + URL 合法性
            if not self._prefilter(raw):
                continue
            # ③ LLM 结构化提取(URL 只许引用原文)
            ann = self._extract_with_llm(raw, province, city,
                                         batch_timestamp, api_key)
            if ann is None:
                continue
            # ④ URL 溯源校验:提取出的 URL 必须存在于原始输入
            if ann.announcement_url not in self._urls_of(raw):
                logger.info("丢弃:url 无法溯源 → %s", ann.announcement_url)
                continue
            # ⑤ 名录验证:高校名必须能匹配教育部名录
            uni = self.registry.match(ann.university)
            if uni is None:
                logger.info("丢弃:高校不在名录中 → %s", ann.university)
                continue
            ann.university = uni["name"]          # 归一化为官方全称
            ann.province, ann.city = uni["province"], uni["city"]
            ann.source = raw.source
            # ⑥ 增强指纹去重
            ann.id = fingerprint(ann.university, ann.announcement_title,
                                 ann.announcement_url, raw.source)
            if ann.id in seen:
                continue
            seen.add(ann.id)
            results.append(ann)
        return results

    def _prefilter(self, raw: RawAnnouncement) -> bool:
        KEYWORDS = ("辅导员", "学生工作", "思政", "班主任")
        if not raw.title or not raw.url:
            return False
        if not raw.url.startswith(("http://", "https://")):
            return False
        if any(p in raw.url for p in ("example.com", "{", "}")):
            return False  # 模板化假 URL
        return any(kw in raw.title for kw in KEYWORDS)
```

第 ④ 层"URL 溯源"是整个方案的**安全性基石**:它是代码级不变量,不依赖 Prompt 自觉。LLM 哪怕幻觉出链接,只要不在原始抓取集合中就会被丢弃。

LLM 提取 Prompt 的对应约束(配合第 ④ 层):

```
注意:
1. announcement_url 字段必须从输入数据中原样引用,严禁自行生成或拼接任何链接;
2. 若输入内容不是高校辅导员招聘公告,返回 {"has_announcement": false};
3. university 使用官方全称,不要使用简称。
```

### 3.4 彻底删除造假逻辑(P0 核心)

| 对象 | 处置 |
|---|---|
| `_generate_city_fallback_snippets`(现第 127-140 行) | **整体删除**。它凭空生成 `https://rsc.{city}.edu.cn/info/counselor` 式假链接,是 D4 的直接来源 |
| 第 122-123 行"结果不足 2 条即触发兜底"的调用点 | 删除,改为记录日志并返回已有结果 |
| `NATIONWIDE_UNIVERSITY_DATABASE`(现第 36-54 行) | **降级保留**:14 条人工收录数据本身可用,但状态文案统一为 "📌 人工收录",与实时抓取的 "🟢 已发布" 区分;数据迁移至 `data/`,代码中永不自动扩充 |
| 空结果 | 返回空列表;API 层附 `"message": "暂未获取到该地区辅导员招聘公告"` 诚实空态,前端展示空态卡片 |

### 3.5 高校名录主数据

```python
# src/registry/university_registry.py
class UniversityRegistry:
    """教育部《全国普通高等学校名单》驱动的只读注册表"""

    @classmethod
    def load(cls, db_path="data/jobhunter.db") -> "UniversityRegistry":
        """优先读 SQLite universities 表,缺失则回退 data/moe_universities.json 快照"""

    def list_by(self, province: str = "all", city: str = "all") -> List[dict]:
        """按省/市返回高校列表 —— 动态替代 CITY_UNIVERSITY_MAP"""

    def match(self, name: str) -> Optional[dict]:
        """四级模糊匹配:精确 → 去后缀(大学/学院/职业) → 编辑距离 ≤ 2 → 别名表"""

    def exists(self, name: str) -> bool: ...
```

**数据来源与更新**:
- `scripts/import_moe_list.py` 读取教育部官网下载的 Excel(字段:学校名称、主管部门、所在地、办学层次、办学性质),写入 SQLite `universities` 表,并导出 `data/moe_universities.json` 快照随仓库分发;
- 运行期只依赖标准库 `sqlite3`/`json`,**不引入 pandas**;导入脚本使用轻量 `openpyxl`(仅开发依赖,不进 `requirements.txt` 运行期亦可);
- 名单每年 6-7 月由教育部更新一次,维护成本极低;
- `CITY_UNIVERSITY_MAP` 整体删除;城市名归一化("芜湖市"→"芜湖")保留为注册表内的小别名表。

> ⚠️ 教育部名单页面与 2024 年版规模(约 3,117 所)在调研报告中标注为 [需验证],导入前需核实最新下载地址。

### 3.6 模型与存储扩展

**模型变更**(`src/models.py`):

```python
class UniversityCounselorAnnouncement(BaseModel):
    ...
    source: str = "unknown"        # 新增:数据来源标识(bing/gaoxiaojob/uni_hr/curated)
    verified: bool = False         # 新增:高校名是否通过名录验证
```

**存储迁移**(`src/db.py`,沿用项目现有的 try/except 迁移风格):

```sql
ALTER TABLE university_counselor_announcements ADD COLUMN source TEXT DEFAULT 'unknown';
ALTER TABLE university_counselor_announcements ADD COLUMN verified INTEGER DEFAULT 0;
```

**指纹升级**:

```python
# 旧:md5(f"{校名}_{省}_{市}_{标题}")[:12]  —— 不含 URL,标题相同即碰撞
# 新:
def fingerprint(university: str, title: str, url: str, source: str) -> str:
    clean_url = re.sub(r'^https?://', '', url).rstrip('/').split('?')[0]
    fp = f"{university.strip()}|{title.strip()}|{clean_url}|{source}"
    return f"ann_{hashlib.md5(fp.encode('utf-8')).hexdigest()[:16]}"
```

**过期标记**(P2):`publish_date` 超过 90 天的公告自动置为 "⚫ 已过期" 状态,前端降权展示。

---

## 4. 分阶段实施计划

### P0 止血(预计 0.5 天)

| 改动 | 文件 | 收益 |
|---|---|---|
| 删除 `_generate_city_fallback_snippets` 及其调用点 | `counselor_adapter.py` | 根除 D4 致命缺陷 |
| 指纹加入 URL、长度 12 → 16 hex | `counselor_adapter.py` | 修复 D5 |
| 新增 `source` / `verified` 字段与迁移 | `models.py`、`db.py` | 来源可追溯 |
| Bing 请求增加超时重试与指数退避 | `counselor_adapter.py` | 缓解 D3 脆弱性 |
| API 返回诚实空态 message | `server.py` | 无数据时不误导用户 |

### P1 多源骨架(预计 3-5 天)

| 改动 | 文件 | 收益 |
|---|---|---|
| 教育部名录导入脚本 + JSON 快照 | `scripts/import_moe_list.py`、`data/moe_universities.json` | 高校主数据 65 → 3,100+ |
| 注册表(省/市索引 + 模糊匹配) | `src/registry/university_registry.py` | 城市覆盖 17 → 300+,零代码扩展 |
| 源契约与聚合器(含四层校验) | `counselor_base.py`、`counselor_aggregator.py` | 多源架构就绪 |
| Bing 逻辑拆分为名录驱动的 site: 定向搜索源 | `counselor_bing.py` | 精准度提升 |
| 高校人才网适配器 | `counselor_gaoxiaojob.py` | 首个权威垂直源(URL 结构先核实) |
| 旧适配器瘦身为 Facade | `counselor_adapter.py` | server/cli 零改动 |
| 测试(见第 5 节) | `tests/` | 回归保障 |

### P2 规模化(预计 1-2 周)

| 改动 | 文件 | 收益 |
|---|---|---|
| 高校人事处直采(URL 发现启发式 + 名录驱动遍历) | `counselor_uni_hr.py` | 第一手公告 |
| 省人社厅事业单位公告源 | `counselor_provincial.py` | 覆盖事业编制公告 |
| 定时采集调度(替代纯用户触发) | `src/scheduler.py` | 数据时效性 |
| 公告过期标记与增量缓存 | `db.py` | 减少重复 LLM 调用 |
| (可选)RSSHub 自建实例监控高校官网 | `docker-compose.yml` | 变更自动感知 |

---

## 5. 测试策略

| 层级 | 覆盖内容 |
|---|---|
| 单元测试 | 指纹归一化(协议/尾斜杠/查询参数)、注册表四级模糊匹配、预过滤关键词与假 URL 拦截、LLM 提取器(mock OpenAI client) |
| **不变量测试** | 构造一批含假 URL 的 mock 抓取结果,断言入库后假数据为 0;即"库中每条公告 url 必可溯源至对应批次 raw 抓取集合" |
| 兼容测试 | 现有 `tests/test_counselor.py`、`tests/test_server.py` 全量通过(Facade 签名不变的验收标准) |
| 网络测试 | `@pytest.mark.network` 标记真实抓取用例(Bing、高校人才网),默认 CI 不执行 |

---

## 6. 风险与合规

1. **外部 URL 未验证**:调研期间网络工具不可用,高校人才网频道路径(如 `/zhaopin/fudaoyuan/`)、教育部名单下载地址均标注 [需验证],P1 编码前须用浏览器/curl 逐一核实,并先检查目标站 `robots.txt`;
2. **Bing 通道定位**:即使重构为 site: 定向搜索,HTML 爬取仍是脆弱通道,定位为"补充源",主力交给垂直平台与人事处直采;
3. **采集卫生**:请求间隔 ≥ 1.5s、串行执行、真实浏览器 UA;政府站点更保守(≥ 3s);5xx 重试不超过 2 次,4xx 不重试;
4. **合规边界**:不采集/存储公告中的联系人姓名、电话等个人信息(《个人信息保护法》第 13 条);保留公告原文链接并注明来源;
5. **LLM 成本**:名录验证前置可过滤大量无关结果,减少无效 LLM 调用;P2 的增量缓存进一步降低重复提取开销。

---

## 7. 附录:新增/修改文件清单

| 文件 | 操作 | 阶段 |
|---|---|---|
| `src/adapters/counselor_adapter.py` | 改造为 Facade,删除造假兜底 | P0 + P1 |
| `src/models.py` | 新增 source/verified 字段 | P0 |
| `src/db.py` | 列迁移、过期标记 | P0 + P2 |
| `src/server.py` | 诚实空态 message | P0 |
| `src/registry/university_registry.py` | 新增 | P1 |
| `src/adapters/counselor_base.py` | 新增 | P1 |
| `src/adapters/counselor_aggregator.py` | 新增 | P1 |
| `src/adapters/counselor_bing.py` | 新增(拆自旧适配器) | P1 |
| `src/adapters/counselor_gaoxiaojob.py` | 新增 | P1 |
| `scripts/import_moe_list.py` | 新增 | P1 |
| `data/moe_universities.json` | 新增(名录快照) | P1 |
| `src/adapters/counselor_uni_hr.py` | 新增 | P2 |
| `src/adapters/counselor_provincial.py` | 新增 | P2 |
| `src/scheduler.py` | 新增 | P2 |
