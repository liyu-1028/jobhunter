# 岗位多维智能匹配数据引擎升级调研报告

> **调研日期**: 2026-07-29  
> **调研对象**: JobHunter 项目 Tab 1「岗位多维智能匹配」模块的数据引擎重构  
> **当前代码入口**: `src/engine.py` → `MultiSourceJobEngine` → `src/adapters/{deepseek_adapter, nowcoder, haitou}.py`  
> **调研目标**: 核实当前引擎缺陷 → 微信搜索渠道技术路线 → 真实岗位数据源矩阵 → 引擎架构升级方案  
> **增量基准**: 本报告基于 [research_job_sources.md](./research_job_sources.md)(以下简称「旧报告」) 的结论增量深化, 不重复其已覆盖的多 LLM 对比与基础适配器架构; 同时对齐 [design_counselor_engine_refactor.md](./design_counselor_engine_refactor.md)(以下简称「辅导员方案」) 已验证的架构范式

---

## 摘要

本报告从五个维度为 JobHunter 岗位引擎升级提供一手调研:

1. **现状核实** — 逐行确认三个适配器(DeepSeek/Nowcoder/Haitou)均为硬编码或 LLM 生成假数据, 无一条真实检索链路;
2. **微信搜索渠道** — 逐一评估搜一搜网页版、搜狗微信、RSSHub、公众号镜像站、Playwright 自动化 5 条路线的可行性与限制;
3. **真实岗位数据源矩阵** — 覆盖 12 类数据源, 产出总评对比表与分阶段推荐;
4. **引擎架构升级方案** — 复用辅导员重构范式(RawJob 契约 → 多源并发 → 校验管线 → 诚实空态), 给出精确到文件的分阶段路线图;
5. **合规与风险** — 爬取法律边界、微信账号风控、LLM 幻觉治理。

**Top 3 推荐数据源**:
1. **面向 LLM 的搜索 API(Tavily/Exa/Serper)** — 覆盖面最广、接入最快、合规风险最低, P0 即可上线
2. **牛客网/应届生求职网/实习僧 校招垂直站** — 结构化程度高, 校招场景第一选择
3. **微信公众号图文解析(RSSHub + LLM 提取管线)** — 内推/一手信息独家渠道, P1 阶段落地

**微信渠道推荐主线**: RSSHub 自建实例 + 第三方镜像站降级 + LLM 二次结构化提取 → 定位为「招聘线索」而非「结构化岗位」

> ⚠️ **调研说明**: 撰写本报告时 WebSearch/WebFetch/curl 等网络工具因权限限制不可用, 外部 URL 与 API 端点均无法实时验证。标注 **[已确认]** 的结论基于源码逐行阅读; 标注 **[需验证]** 的 URL、API 路径与价格来自调研者训练知识(截止 2025 年初), 建议在实施前用浏览器或 curl 逐一核实; 标注 **[推测]** 的为基于合理推断的建议。

---

## 1. 现状缺陷核实(基于源码逐行确认)

### 1.1 D1: Nowcoder 适配器为纯硬编码假数据 — [已确认]

**代码位置**: `src/adapters/nowcoder.py` 全文(80 行)

逐行确认:
- 第 19 行注释自述: `# 模拟牛客网实时校招日历与企业名企内推专场数据`
- 第 19-77 行: 3 条 `JobItem` 全部为手工拼接的 Python 字面量, 公司固定为「美团」「拼多多」「商汤科技」, 没有任何 HTTP 请求、API 调用或页面解析逻辑
- `match_score` 硬编码为 94/92/89, 与牛客网无关
- `apply_url` 直接写公司招聘官网首页(`https://zhaopin.meituan.com`), 并非具体岗位投递链接
- `recommend_reason` 包含「牛客校招热度榜 TOP3」等虚构文案

**结论**: `NowcoderAdapter` 与牛客网无任何数据交互, 产出的岗位为纯静态假数据。

### 1.2 D2: Haitou 适配器为纯硬编码假数据 — [已确认]

**代码位置**: `src/adapters/haitou.py` 全文(61 行)

- 第 18 行注释自述: `# 模拟海投网校招与宣讲会聚合数据`
- 第 19-58 行: 2 条 `JobItem`, 公司固定为「网易集团」「招商银行网络科技」, 同样无任何网络请求
- 结构与 nowcoder.py 完全一致, 仅公司名和文案不同

**结论**: `HaitouAdapter` 与海投网无任何数据交互。

### 1.3 D3: DeepSeek 适配器实质是「LLM 生成」而非「检索」 — [已确认]

**代码位置**: `src/deepseek_client.py` 全文(251 行)

两种运行模式的实质:

| 模式 | 触发条件 | 实质 | 数据真实性 |
|---|---|---|---|
| API 模式 | 有 `DEEPSEEK_API_KEY` | 向 DeepSeek 发送用户 Profile, 要求 LLM **生成**匹配岗位 JSON | **LLM 幻觉**: 模型无法实时联网检索, 只能凭训练数据编造岗位, 薪资/链接/部门信息均不可信 |
| Mock 模式 | 无 Key 或 API 异常 | 本地硬编码 6 条假岗位(腾讯/阿里/字节/华为/中国移动/微软) | **纯假数据**: 第 129 行注释 `# 开启 Demo Mock 模式` |

DeepSeek 的 system prompt(第 32-61 行)要求模型「检索并匹配」, 但 `deepseek-chat` 模型本身不具备联网搜索能力([需验证]: DeepSeek 是否在 2025 下半年新增了联网搜索 function calling), 因此 prompt 中的「检索」只是角色扮演, 产出的岗位名称、薪资、推荐理由均为模型臆造。

**关键问题**: Mock 模式产出的腾讯/阿里/字节等大厂岗位以「真实岗位」身份入库(`db.save_jobs`), 前端无任何标记区分真假, 用户可能据此做出错误求职决策。

### 1.4 D4: 指纹去重粒度不足 — [已确认]

**代码位置**: `src/adapters/base.py` 第 21-28 行

```python
def generate_fingerprint(self, job: JobItem) -> str:
    company = (job.company or "").strip().lower()
    title = (job.title or "").strip().lower()
    location = (job.location or "").strip().lower()
    raw_key = f"{company}_{title}_{location}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()
```

缺陷清单:
1. **不含 URL**: 同一公司同一岗位在不同平台发布(各有不同链接)会被去重丢弃, 而实际上可能是不同批次/不同部门的岗位
2. **不含来源**: 与辅导员引擎的旧指纹犯同一错误(已在 `counselor_base.py` 的 `fingerprint()` 中修复为含 URL+来源的 4 元组)
3. **无 URL 归一化**: 协议前缀(http/https)、尾斜杠、查询参数差异都会导致同一岗位产生不同指纹
4. **无来源追溯**: `JobItem.source` 字段虽然存在于模型中, 但指纹去重时完全不使用, 导致跨源合并后无法知道某条岗位来自哪个源

### 1.5 D5: JobItem 模型字段不足以承载真实抓取数据 — [已确认]

**代码位置**: `src/models.py` 第 16-31 行

| 字段 | 现状 | 缺陷 |
|---|---|---|
| `source: str = "deepseek"` | 默认值为 "deepseek", 所有适配器共享同一默认值 | 多源合并时来源标识混乱 |
| `apply_url: str = "#"` | 默认值为 "#" | 当源无法提供 URL 时静默使用假值, 不触发校验 |
| 缺少 `raw_url` 字段 | — | 无法区分「岗位详情页 URL」与「投递 URL」 |
| 缺少 `description` 字段 | — | 无法存储岗位原始描述正文(供 LLM 二次提取) |
| 缺少 `publish_date` 字段 | — | 无法标记岗位时效性, 过期岗位永不淘汰 |
| 缺少 `verified` 字段 | — | 无法标记岗位是否通过溯源校验(对标辅导员模型的 `verified` 字段) |
| `fetched_at: str = ""` | 仅在 server.py 层回填 | 源适配器本身不感知时间戳 |

**与辅导员模型对比**: `UniversityCounselorAnnouncement` 已有 `source`、`verified`、`publish_date`、`announcement_url` 溯源字段, 岗位模型需对齐。

### 1.6 D6: 引擎无校验管线 — [已确认]

**代码位置**: `src/engine.py` 第 21-60 行

`MultiSourceJobEngine.search_all_sources` 的逻辑: 并发抓取 → 指纹去重 → 排序 → 返回。缺失环节:
- **无预过滤**: 不校验 URL 合法性、不检查关键词匹配
- **无 URL 溯源**: 不验证 `apply_url` 是否来自真实抓取
- **无 LLM 结构化提取**: 适配器直接产出最终 `JobItem`, 绕过了结构化校验
- **无诚实空态**: 即使所有源都失败, 引擎仍返回空列表而不附带提示信息(server.py 第 120-126 行也无空态处理)

---

## 2. 微信搜索渠道调研(核心专题)

> 旧报告第 2 节已覆盖 RSSHub、搜狗微信、Playwright、聚合站四条路线的定性分析。本节增量深化: 逐一评估各路线的**真实入口 URL、可访问性、反爬现状、字段覆盖、工程成本**, 并给出推荐主线与降级链。

### 2.1 微信搜一搜网页版

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://search.weixin.qq.com` [需验证] — 微信搜一搜的网页端入口, 可能需要微信扫码登录后才能使用; 另有说法称搜一搜目前仅在微信客户端内可用, 无独立网页版 [需验证] |
| **页面形态** | 搜索结果列表, 包含公众号文章、朋友圈、品牌账号等混合结果 [需验证] |
| **可访问性** | 高度依赖微信登录态; 网页版可能需要扫码授权, 不适合无头服务器自动化 |
| **反爬** | 微信生态的风控极其严格, IP 频率限制 + 账号封禁双重机制 [需验证] |
| **字段覆盖** | 搜索结果含标题、摘要、公众号名称、发布时间 — 基本满足招聘线索发现, 但缺少结构化岗位字段 |
| **工程成本** | 极高: 需维持微信登录态 + 应对验证码 + 应对账号风控 |

**结论**: 不推荐作为自动化数据源。搜一搜更适合作为「人工调研入口」而非「自动抓取通道」。

### 2.2 搜狗微信搜索

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://weixin.sogou.com/` — 搜狗搜索引擎的微信公众号文章搜索入口 [需验证: 2025-2026 年是否仍然在线] |
| **搜索机制** | 输入关键词 → 返回公众号文章列表(标题、摘要、公众号名、发布时间) |
| **反爬现状** | 旧报告已指出「反爬极其严重(验证码拦截、Cookie 过期快)」; 2024 年后搜狗搜索整体并入腾讯生态, 微信搜索入口可能进一步收紧 [需验证] |
| **可访问性** | 首页可能正常加载, 但翻页和批量查询极易触发验证码(滑块验证) [需验证] |
| **字段覆盖** | 标题 + 摘要 + 公众号名 + 文章链接(跳转 mp.weixin.qq.com) — 可作为招聘线索 |
| **工程成本** | 高: 需维护 Cookie 池 + 验证码破解(或人工干预) + 低频抓取(≤ 1 次/分钟) |

**结论**: 可作为**降级备选**, 但不作为主线。频率控制在极低水平(每天 ≤ 50 次查询), 配合代理 IP 池。

### 2.3 RSSHub 微信公众号路由

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://docs.rsshub.app/routes/social-media#wei-xin` [需验证] — RSSHub 官方文档中微信相关路由说明 |
| **路由机制** | RSSHub 提供多种微信路由 [需验证]: <br>① `/wechat/mp/:id` — 公众号文章列表(依赖第三方镜像源如 chuansongme.com 或 wxnmh.com) <br>② `/wechat/mp/homepage/:id` — 公众号合集 <br>③ `/wechat/mp/msgalbum/:id` — 公众号文章专辑 |
| **核心限制** | 所有微信路由**均依赖第三方镜像站**, 因微信官方无公开 API; 镜像站的可用性不稳定(随时可能下线) [需验证] |
| **公共实例** | `rsshub.app` 公共节点对微信路由限流严重, 基本不可用; 必须**自建 RSSHub 实例** |
| **自建成本** | Docker 部署 `docker run -d -p 1200:1200 diygod/rsshub` [需验证镜像名], 约 10 分钟完成; 需配置镜像源 API Key(若有) |
| **字段覆盖** | RSS 条目含标题、链接、发布时间、摘要 — 满足招聘线索发现 |
| **工程成本** | 中等: 自建 RSSHub 实例 + 监控镜像源可用性 + 定期拉取(建议 1-2 次/天) |

**结论**: **推荐为微信渠道主线**。自建 RSSHub 实例配合招聘类公众号订阅列表(如「校招薪水」「互联网内推日报」「offershow」等 [需验证: 具体公众号名单需人工筛选]), 每日定时拉取, 是最稳定的微信内容获取方式。

### 2.4 第三方公众号聚合站/镜像站

| 维度 | 评估 |
|---|---|
| **代表站点** | 传送门(chuansongme.com) [需验证: 2025-2026 是否仍在线]、微信年华(wxnmh.com) [需验证]、搜狗微信搜索结果缓存 |
| **可抓取性** | 聚合站通常反爬较宽松(普通 HTTP 即可), 但站点存活期不可控 — 经常因版权或微信压力下线 |
| **字段覆盖** | 标题 + 正文全文 + 发布时间 + 公众号名 — 比 RSS 更完整 |
| **工程成本** | 低至中: 简单 HTTP 抓取即可, 但需维护镜像站可用性监控 + 多源降级 |

**结论**: 作为 RSSHub 的**降级备选**。当 RSSHub 依赖的镜像源下线时, 可直接爬取其他聚合站。建议维护 2-3 个镜像源的 fallback 链。

### 2.5 Playwright/浏览器自动化抓取搜一搜

| 维度 | 评估 |
|---|---|
| **技术方案** | 使用 Playwright 模拟真实用户操作微信客户端内的搜一搜, 或 PC 微信桌面端 |
| **登录态** | 需定期人工扫码保持微信登录态(约 1-3 天过期一次 [需验证]) |
| **风控风险** | **极高**: 微信对自动化行为检测极严, 可能导致账号被封禁或限制搜索功能 [需验证] |
| **数据完整性** | 搜索结果最完整(含文章、公众号、小程序等全生态结果) |
| **工程成本** | 极高: Playwright 部署 + 登录态维护 + 风控应对 + 验证码处理 |

**结论**: **不推荐**。账号风控风险过高, 且有违反《微信公众平台服务协议》关于自动化访问的条款。仅建议在 P2 阶段作为实验性探索。

### 2.6 微信渠道总结: 推荐主线与降级链

```
推荐主线:
  RSSHub 自建实例 → 订阅招聘类公众号列表 → 定时拉取(1-2 次/天)
  → LLM 二次结构化提取(公司/岗位/城市/薪资/投递方式)
  → 定位为「招聘线索」, 非结构化岗位数据

降级链:
  RSSHub 镜像源不可用 → 直接爬取第三方聚合站(chuansongme/wxnmh 等)
  → 聚合站全部不可用 → 搜狗微信搜索(极低频, ≤ 50 次/天)
  → 搜狗不可用 → 降级为空, 记录日志
```

**关键定位**: 微信内容(公众号文章)产出的是**招聘线索**(如「字节跳动 2026 秋招内推码: xxx, 岗位: 后端/前端/算法, 投递链接: https://...」), 而非结构化岗位数据。需要 LLM 二次提取管线将非结构化图文转为 `RawJob` 格式。这与旧报告第 2.2 节的「LLM 结构化提取流程」一致。

---

## 3. 真实岗位数据源矩阵

> 旧报告第 3 节已覆盖牛客网、海投网、大厂官网、Crawl4AI 等基础分析。本节增量深化: 逐一核实各源的实际 API 端点、反爬难度、合规风险, 并产出总评对比表。

### 3.1 校招垂直平台

#### 3.1.1 牛客网(nowcoder.com)

| 维度 | 评估 |
|---|---|
| **Web 端岗位栏目** | `https://www.nowcoder.com/jobs` [需验证] — 牛客网招聘频道, 含校招日历、名企内推专场 |
| **移动端/API** | 牛客网 APP 内「求职」tab 有校招岗位聚合; 移动端 API 端点如 `https://www.nowcoder.com/nccommon/jobs/search` [需验证] 可能返回 JSON |
| **校招日历** | `https://www.nowcoder.com/school/calendar` [需验证] — 按时间线展示各公司校招批次 |
| **反爬** | 中等: 需登录态查看完整岗位详情, 列表页可能无需登录; 有 Cloudflare 或类似 WAF [需验证] |
| **字段覆盖** | 公司名、岗位名、城市、薪资范围、招聘批次 — 高度结构化 |
| **合规风险** | 低: 公开展示的校招信息, 正常频率抓取属于合理使用 |

#### 3.1.2 应届生求职网(yingjiesheng.com)

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://www.yingjiesheng.com/` [需验证] — 老牌校招信息聚合站 |
| **栏目结构** | 按城市/行业/公司性质分类; 有「校招专场」「名企校招」等板块 [需验证] |
| **API/RSS** | 无公开 API; 可能有 RSS(早期站点常用) [需验证] |
| **反爬** | 低: 传统 CMS 站点, HTML 解析即可, 反爬措施较弱 [需验证] |
| **字段覆盖** | 公司名、岗位名、城市、发布时间 — 结构化程度中等 |

#### 3.1.3 实习僧(shixiseng.com)

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://www.shixiseng.com/` [需验证] — 实习岗位垂直平台 |
| **开放 API** | 无公开 API; 搜索结果页通过 AJAX 加载, 可逆向其内部 JSON 接口 [需验证] |
| **反爬** | 中等: 搜索结果需要 JS 渲染, 列表接口可能有签名校验 [需验证] |
| **字段覆盖** | 公司名、岗位名、城市、薪资、实习时长 — 高度结构化 |

### 3.2 主流招聘平台(高风险, 不推荐直爬)

#### 3.2.1 Boss 直聘(zhipin.com)

| 维度 | 评估 |
|---|---|
| **反爬** | **极高**: 字体反爬(岗位名/薪资使用自定义字体加密)、设备指纹、行为分析、IP 黑名单 [需验证] |
| **法律风险** | **高**: Boss 直聘(华品招聘)曾多次发起反不正当竞争诉讼。2021 年北京海淀法院判决某爬虫公司赔偿 Boss 直聘 50 万元 [需验证: 具体案号与金额]; 2023 年多起类似案件 [需验证] |
| **结论** | **不推荐直爬**。法律风险与反爬成本均过高。如需 Boss 直聘数据, 建议通过面向 LLM 的搜索 API 间接获取 |

#### 3.2.2 拉勾(lagou.com)/ 猎聘(liepin.com)/ 智联(zhaopin.com)/ 前程无忧(51job.com)

| 维度 | 评估 |
|---|---|
| **反爬** | 高: 各平台均有不同程度的反爬措施(JS 渲染、验证码、IP 限制) [需验证] |
| **法律风险** | 中高: 各平台用户协议明确禁止自动化抓取; 《反不正当竞争法》第 12 条(互联网专条)可作为起诉依据 |
| **结论** | **不推荐直爬**。同上, 通过搜索 API 间接获取更安全 |

### 3.3 政府与公共就业服务平台

#### 3.3.1 国家大学生就业服务平台(ncss.cn / ncss.org.cn)

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://www.ncss.cn/` 或 `https://www.ncss.org.cn/` [需验证] — 教育部主管的大学生就业服务平台 |
| **岗位栏目** | 「职位信息」「招聘会」「专场招聘」等板块 [需验证] |
| **反爬** | 低: 政府公益平台, 通常无强反爬 [需验证] |
| **字段覆盖** | 公司名、岗位名、城市、发布时间 — 结构化程度中等 |
| **合规** | 低风险: 政府公开信息, 正常频率抓取 |

#### 3.3.2 高校人才网(gaoxiaojob.com)

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://www.gaoxiaojob.com/` [需验证] — 已在辅导员模块使用 |
| **岗位栏目** | 除辅导员外, 也有高校行政、科研岗位 [需验证] |
| **反爬** | 低: 传统 CMS, HTML 解析即可 [需验证] |
| **适用场景** | 高校岗位(含行政/科研/教学), 与 Tab 1 的互联网校招场景互补 |

### 3.4 面向 LLM 的搜索 API

| API | 核心优势 | 中文覆盖 | 价格 | 接入成本 | 推荐度 |
|---|---|---|---|---|---|
| **Tavily** (`tavily.com`) | 专为 LLM Agent 设计的搜索 API, 返回清洗后的正文片段, 支持 JSON Mode [需验证] | 中等: 中文搜索质量不如英文 [需验证] | 免费 1000 次/月, Pro $0.004/次 [需验证] | 低: `pip install tavily-python` | ⭐⭐⭐⭐ |
| **Exa.ai** (`exa.ai`) | 语义搜索引擎, 可按域名/时间/内容类型过滤, 对 LLM 友好 [需验证] | 中等 [需验证] | 免费 1000 次/月, 付费 $5/1000 次 [需验证] | 低 | ⭐⭐⭐ |
| **Serper** (`serper.dev`) | Google 搜索结果 API, 返回标准 Google SERP JSON [需验证] | 较好: Google 中文搜索质量高 | 免费 2500 次, 付费 $50/50000 次 [需验证] | 低 | ⭐⭐⭐⭐⭐ |
| **SerpAPI** (`serpapi.com`) | 多搜索引擎聚合(Google/Bing/Yahoo 等) [需验证] | 较好 | 免费 100 次/月, 付费 $50/5000 次 [需验证] | 低 | ⭐⭐⭐ |
| **Bing Web Search API** | 微软官方 API, 有 Azure 免费层 [需验证] | 较好 | Azure 免费层 S1: 3 次/秒, 1000 次/月 [需验证] | 低 | ⭐⭐⭐⭐ |

**推荐**: **Serper + Tavily 双源组合**作为 P0 首选。Serper 提供 Google 搜索的高质量中文结果, Tavily 提供 LLM 友好的正文提取。两者配合可覆盖大部分公开招聘信息。

### 3.5 远程/独立工作平台

#### 3.5.1 电鸭社区(eleduck.com)

| 维度 | 评估 |
|---|---|
| **入口 URL** | `https://eleduck.com/` [需验证] — 中文远程工作社区 |
| **API/RSS** | 无公开 API; 可能有 RSS feed [需验证] |
| **反爬** | 低: 社区型站点, 内容公开展示 [需验证] |
| **字段覆盖** | 公司名、岗位名、工作类型(远程/混合)、薪资 — 结构化程度中等 |
| **适用场景** | 远程工作/数字游民岗位, 作为补充源 |

### 3.6 大厂官方招聘 API

| 公司 | 招聘官网 | API 端点(推测) | 反爬 | 合规 |
|---|---|---|---|---|
| 腾讯 | `https://join.qq.com` | `/api/v1/jobs` 类接口 [需验证] | 低: 自家平台, 展示性接口 | 低: 公开的招聘信息 |
| 阿里 | `https://talent.alibaba.com` | 前后端分离, 有 JSON 接口 [需验证] | 低 | 低 |
| 字节 | `https://jobs.bytedance.com` | `/api/v1/jobs/search` [需验证] | 低 | 低 |
| 华为 | `https://career.huawei.com` | 可能有 JSON 接口 [需验证] | 低 | 低 |
| 百度 | `https://talent.baidu.com` | 前后端分离 [需验证] | 低 | 低 |

**策略**: 大厂官网的校招接口通常前后端分离, 在浏览器 Network 面板即可抓到 JSON API。每个大厂写一个轻量 Adapter 即可。这是**最稳定、最合规、最结构化**的数据来源。

### 3.7 数据源总评对比表

| 数据源 | 权威性 | 覆盖度 | 结构化 | 反爬难度 | 合规风险 | 推荐阶段 |
|---|---|---|---|---|---|---|
| Serper/Google 搜索 API | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐(需 LLM 提取) | ⭐(无需爬) | ⭐(极低) | **P0** |
| Tavily 搜索 API | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐(LLM 友好) | ⭐(无需爬) | ⭐(极低) | **P0** |
| 大厂官方招聘 API | ⭐⭐⭐⭐⭐ | ⭐⭐⭐(垂直) | ⭐⭐⭐⭐⭐ | ⭐⭐(低) | ⭐(极低) | **P0** |
| 牛客网 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐(校招) | ⭐⭐⭐⭐ | ⭐⭐⭐(中) | ⭐⭐(低) | **P1** |
| 应届生求职网 | ⭐⭐⭐ | ⭐⭐⭐⭐(校招) | ⭐⭐⭐ | ⭐⭐(低) | ⭐⭐(低) | **P1** |
| 实习僧 | ⭐⭐⭐ | ⭐⭐⭐(实习) | ⭐⭐⭐⭐ | ⭐⭐⭐(中) | ⭐⭐(低) | **P1** |
| 国家大学生就业服务平台 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐(低) | ⭐(极低) | **P1** |
| 微信公众号(RSSHub) | ⭐⭐⭐ | ⭐⭐⭐(内推/独家) | ⭐⭐(需 LLM 提取) | ⭐⭐⭐(中) | ⭐⭐⭐(中) | **P1** |
| 电鸭社区 | ⭐⭐ | ⭐⭐(远程) | ⭐⭐⭐ | ⭐(低) | ⭐(极低) | **P2** |
| Boss 直聘/拉勾/猎聘 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐(极高) | ⭐⭐⭐⭐⭐(极高) | **不推荐** |
| 搜狗微信搜索 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐(高) | ⭐⭐⭐(中) | **P2(降级)** |

---

## 4. 引擎架构升级方案

### 4.1 对齐辅导员重构范式

辅导员引擎重构(`design_counselor_engine_refactor.md`)已验证了以下架构范式:

```
RawAnnouncement 契约 → 多源并发 → 校验管线(预过滤→LLM提取→URL溯源→名录验证→指纹去重) → 诚实空态
```

岗位引擎升级**完全复用此范式**, 仅将领域概念替换:

| 辅导员范式 | 岗位范式 |
|---|---|
| `RawAnnouncement` | `RawJob` |
| `BaseCounselorSource` | `BaseJobSource` |
| `CounselorAggregator` | `JobAggregator` |
| `UniversityRegistry` | `CompanyRegistry`(可选, 用于公司名归一化) |
| 辅导员关键词过滤 | 岗位关键词过滤 + 匹配度评分 |
| 名录验证 | URL 溯源 + 公司名归一化(无权威名录, 弱校验) |

### 4.2 目标架构

```
┌────────────────────────────────────────────────────────────┐
│ /api/search_jobs   (Facade 保持, server.py 零改动)          │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ JobSearchAdapter(瘦身为 Facade, 保留原方法签名)              │
│   └── JobAggregator                                        │
│         ├── [并发] ThreadPoolExecutor 调度各 Source          │
│         │     ├── SerperSearchSource     (P0 新增)          │
│         │     ├── TavilySearchSource     (P0 新增)          │
│         │     ├── BigTechOfficialSource  (P0 新增: 大厂 API)│
│         │     ├── NowcoderRealSource     (P1 替换: 真牛客)  │
│         │     ├── YingjieshengSource     (P1 新增)          │
│         │     ├── ShixisengSource        (P1 新增)          │
│         │     ├── NcssSource             (P1 新增)          │
│         │     ├── WeChatRSSSource        (P1 新增: RSSHub)  │
│         │     └── EleduckSource          (P2 新增)          │
│         └── [串行] 校验管线                                   │
│               ① 关键词预过滤(匹配用户 Profile 关键词)        │
│               ② URL 合法性校验(拒绝假 URL / 模板 URL)       │
│               ③ LLM 结构化提取(公司/岗位/城市/薪资/要求)    │
│               ④ URL 溯源校验(URL 必须存在于原始抓取集合)     │
│               ⑤ 公司名归一化(可选, CompanyRegistry)          │
│               ⑥ 匹配度重评分(DeepSeek 作为评分器)           │
│               ⑦ 增强指纹去重(公司|岗位|URL|来源)            │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│ RawJob 契约(所有源只产出原始数据, 不产出最终 JobItem)        │
│ JobDatabase(扩展: description / publish_date / verified)     │
│ 诚实空态(无结果时明确告知, 不编造)                           │
└────────────────────────────────────────────────────────────┘
```

### 4.3 DeepSeek 的新定位: 从「数据生产者」降级为「提取与评分器」

当前架构的根本问题: DeepSeek 同时扮演「数据源」和「结构化引擎」两个角色 — 它既"生产"岗位数据, 又对数据进行结构化。这导致 LLM 幻觉直接以"真实岗位"身份入库。

**新定位**:

| 角色 | 当前 | 重构后 |
|---|---|---|
| 数据生产者 | DeepSeek(生成假岗位) | **删除**: 真实数据源(Serper/Tavily/大厂 API 等) |
| 结构化提取器 | 无(适配器直接返回 JobItem) | **新增**: DeepSeek 从 RawJob 提取结构化字段 |
| 匹配度评分器 | 无(硬编码 match_score) | **新增**: DeepSeek 根据用户 Profile 对岗位评分 |

```python
# DeepSeek 的新职责 1: 结构化提取 (校验管线第 ③ 步)
EXTRACTION_PROMPT = """你是一个招聘信息结构化提取专家。
请从给定的招聘文本中提取字段, 严格输出 JSON:
{
  "is_job_posting": true,
  "company": "公司官方全称",
  "title": "岗位名称",
  "location": "工作城市",
  "salary": "薪资范围(无法确定时返回空字符串)",
  "requirements": ["要求1", "要求2", "要求3"],
  "batch": "招聘批次(如 2026届秋招)",
  "company_type": "公司性质(互联网/国企/外企等)",
  "description": "岗位描述简述"
}
规则:
1. 不要输出任何 URL, 链接由系统回填;
2. 如果输入内容不是招聘信息, 返回 {"is_job_posting": false};
3. 只提取文本中明确出现的信息, 不要推测或补充。"""

# DeepSeek 的新职责 2: 匹配度评分 (校验管线第 ⑥ 步)
SCORING_PROMPT = """你是一个专业的求职匹配评估专家。
请根据求职者背景评估以下岗位的匹配度, 输出 JSON:
{
  "match_score": 0-100 的整数,
  "recommend_reason": "推荐理由(50字内)",
  "match_highlights": ["匹配点1", "匹配点2"]
}
求职者背景: {profile_summary}
岗位信息: {job_summary}"""
```

### 4.4 用户 Profile 多维条件的「全面搜索」建模

用户要求「全面搜索岗位或公司的条件」, 需要将 `UserProfile` 的多维条件展开为多个搜索 query:

```python
class QueryExpander:
    """将用户多维 Profile 展开为多组搜索 query, 覆盖不同搜索意图."""

    def expand(self, profile: UserProfile) -> List[str]:
        """生成多 query 列表, 覆盖关键词 × 行业 × 城市 × 批次的组合."""
        queries = []
        keywords = [k.strip() for k in profile.keywords.split(",")]
        locations = [l.strip() for l in profile.location.split("/")]

        # 策略 1: 关键词 + 城市 + 校招 (精准匹配)
        for kw in keywords[:3]:  # 最多取 3 个关键词
            for loc in locations[:3]:
                queries.append(f"{kw} {loc} {profile.batch} 招聘")

        # 策略 2: 行业 + 公司性质 (泛匹配)
        queries.append(f"{profile.target_industry} {profile.company_type} {profile.batch}")

        # 策略 3: 学校 + 内推 (校友网络)
        queries.append(f"{profile.school} {profile.batch} 内推")

        # 策略 4: 大厂定向 (site: 搜索)
        for domain in ["join.qq.com", "talent.alibaba.com", "jobs.bytedance.com"]:
            queries.append(f"site:{domain} {keywords[0]} {profile.batch}")

        return queries  # 预计 8-15 条 query
```

### 4.5 核心数据模型扩展

```python
# src/adapters/job_base.py — 对标 counselor_base.py

from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class RawJob:
    """各数据源返回的统一原始格式 — 未经 LLM 提取的原始抓取结果."""
    title: str
    url: str                   # 必须是源实际抓到的链接, 禁止源自行拼接/推测
    snippet: str = ""          # 摘要或正文片段, 供 LLM 提取
    company: str = ""          # 源能直接获取的公司名(大厂 API 等结构化源)
    location: str = ""
    salary: str = ""
    publish_date: str = ""
    source: str = ""           # serper / tavily / bigtech / nowcoder / wechat_rss / ...
    meta: Dict = field(default_factory=dict)  # 结构化源的附加字段


import re, hashlib

def job_fingerprint(company: str, title: str, url: str, source: str) -> str:
    """增强版指纹: 含归一化 URL 与来源, 16 位 hex."""
    clean_url = re.sub(r"^https?://", "", (url or "").strip()).rstrip("/").split("?")[0]
    fp = f"{(company or '').strip().lower()}|{(title or '').strip().lower()}|{clean_url}|{(source or '').strip()}"
    return f"job_{hashlib.md5(fp.encode('utf-8')).hexdigest()[:16]}"
```

**JobItem 模型扩展**(`src/models.py`):

```python
class JobItem(BaseModel):
    id: str
    title: str
    company: str
    company_type: str = ""
    company_size: str = ""
    location: str
    salary: str = "面议"
    batch: str = ""
    match_score: int = 0
    recommend_reason: str = ""
    requirements: List[str] = []
    tags: List[str] = []
    apply_url: str = ""         # 改为空字符串, 便于校验管线拦截假值
    source: str = "unknown"     # 默认改为 "unknown", 不再默认 "deepseek"
    fetched_at: str = ""
    # ---- 新增字段 ----
    description: str = ""       # 岗位原始描述(供前端展开)
    publish_date: str = ""      # 岗位发布时间
    verified: bool = False      # 是否通过 URL 溯源校验
```

### 4.6 校验管线伪代码

```python
# src/adapters/job_aggregator.py

class JobAggregator:
    """多源聚合器: 替代旧版 MultiSourceJobEngine."""

    def __init__(self, sources, api_key=None):
        self.sources = sources
        self.api_key = api_key

    def run(self, profile: UserProfile, batch_timestamp=None) -> List[JobItem]:
        batch_timestamp = batch_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ① 并发抓取所有源 (QueryExpander 展开多 query, 各源自行选择 query 策略)
        raw_all = self._collect(profile)

        llm = DeepSeekJobHunter(api_key=self.api_key)
        results, seen = [], set()

        for raw in raw_all:
            # ② 预过滤: URL 合法性 + 关键词粗匹配
            if not self._prefilter(raw, profile):
                continue
            # ③ LLM 结构化提取 (只提取, 不生成 URL)
            job = self._extract_with_llm(raw, profile, batch_timestamp, llm)
            if job is None:
                continue
            # ④ URL 溯源: apply_url 必须等于 raw.url (LLM 永不产出 URL)
            if job.apply_url != raw.url:
                continue
            # ⑤ 匹配度评分 (DeepSeek 根据 Profile 打分)
            job = self._score_match(job, profile, llm)
            # ⑥ 增强指纹去重
            job.id = job_fingerprint(job.company, job.title, job.apply_url, raw.source)
            if job.id in seen:
                continue
            seen.add(job.id)
            job.source = raw.source
            job.verified = True
            results.append(job)

        # 按匹配度降序排列
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

    def _prefilter(self, raw: RawJob, profile: UserProfile) -> bool:
        if not raw.title or not raw.url:
            return False
        if not raw.url.startswith(("http://", "https://")):
            return False
        if any(p in raw.url for p in ("example.com", "{", "}", " ")):
            return False
        # 关键词粗匹配: 标题或摘要至少包含一个用户关键词
        keywords = [k.strip() for k in profile.keywords.split(",")]
        text = f"{raw.title} {raw.snippet} {raw.company}"
        return any(kw in text for kw in keywords)
```

### 4.7 兼容迁移路径

**核心原则**: Facade 保持, `/api/search_jobs` 零改动。

```python
# src/adapters/job_search_adapter.py — 新 Facade, 替代 DeepSeekAdapter/NowcoderAdapter/HaitouAdapter

class JobSearchAdapter:
    """兼容旧接口的 Facade. server.py 零改动."""

    def __init__(self, api_key=None):
        self.aggregator = JobAggregator(
            sources=[SerperSearchSource(), TavilySearchSource(), BigTechOfficialSource()],
            api_key=api_key,
        )

    def search_all_sources(self, profile: UserProfile) -> SearchResult:
        """方法签名与 MultiSourceJobEngine.search_all_sources 一致."""
        jobs = self.aggregator.run(profile)
        return SearchResult(
            search_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_found=len(jobs),
            jobs=jobs,
        )
```

**server.py 改动**(极小):

```python
# 旧:
from src.engine import create_default_engine
default_engine = create_default_engine()
# ...
search_res = active_engine.search_all_sources(user_prof)

# 新:
from src.adapters.job_search_adapter import JobSearchAdapter
default_engine = JobSearchAdapter()
# ...
# 仅需将 create_default_engine(api_key=...) 改为 JobSearchAdapter(api_key=...)
# 其余代码零改动, 因为 search_all_sources() 签名一致
```

### 4.8 目录结构变化

```
src/
├── adapters/
│   ├── base.py                  # 保留, 但标记为 deprecated (旧接口兼容)
│   ├── job_base.py              # 新增: RawJob + BaseJobSource + job_fingerprint
│   ├── job_aggregator.py        # 新增: 多源并发 + 校验管线
│   ├── job_search_adapter.py    # 新增: Facade, 替代 engine.py
│   ├── query_expander.py        # 新增: Profile → 多 query 展开
│   ├── serper_source.py         # 新增(P0): Serper Google 搜索
│   ├── tavily_source.py         # 新增(P0): Tavily LLM 搜索
│   ├── bigtech_source.py        # 新增(P0): 大厂官方 API 聚合
│   ├── nowcoder_real.py         # 新增(P1): 替换硬编码假数据
│   ├── yingjiesheng_source.py   # 新增(P1): 应届生求职网
│   ├── shixiseng_source.py      # 新增(P1): 实习僧
│   ├── ncss_source.py           # 新增(P1): 国家大学生就业服务平台
│   ├── wechat_rss_source.py     # 新增(P1): RSSHub 微信路由
│   ├── eleduck_source.py        # 新增(P2): 电鸭社区
│   ├── deepseek_adapter.py      # 保留(标记 deprecated), 不再注册到引擎
│   ├── nowcoder.py              # 保留(标记 deprecated), P1 后删除
│   └── haitou.py                # 保留(标记 deprecated), P1 后删除
├── engine.py                    # 改造: 委托 JobAggregator, 保留类名兼容
├── models.py                    # 改造: JobItem 新增 description/publish_date/verified
└── db.py                        # 改造: 新增列迁移 + 过期标记
```

---

## 5. 分阶段实施路线图

### P0 止血(预计 1-2 天): 删除假数据 + 接入搜索 API

| 改动 | 文件 | 收益 |
|---|---|---|
| 新增 `RawJob`、`BaseJobSource`、`job_fingerprint` | `src/adapters/job_base.py` | 数据契约就绪 |
| 新增 `QueryExpander`(Profile → 多 query) | `src/adapters/query_expander.py` | 全面搜索建模 |
| 新增 `SerperSearchSource`(Google 搜索 JSON) | `src/adapters/serper_source.py` | **首个真实数据源** |
| 新增 `TavilySearchSource`(LLM 友好搜索) | `src/adapters/tavily_source.py` | **第二个真实数据源** |
| 新增 `BigTechOfficialSource`(腾讯/阿里/字节校招 API) | `src/adapters/bigtech_source.py` | **大厂真实校招岗位** |
| 新增 `JobAggregator`(并发 + 校验管线) | `src/adapters/job_aggregator.py` | 校验管线就绪 |
| 新增 `JobSearchAdapter`(Facade) | `src/adapters/job_search_adapter.py` | server.py 零改动 |
| 改造 `engine.py` 委托 `JobAggregator` | `src/engine.py` | 旧引擎平滑过渡 |
| 模型扩展: `description`/`publish_date`/`verified` | `src/models.py` | 字段对齐辅导员模型 |
| DB 列迁移 + 过期标记 | `src/db.py` | 数据持久化扩展 |
| server.py: 诚实空态 message | `src/server.py` | 无数据时不误导 |
| 删除 `DeepSeekAdapter` 的注册(不再作为数据源) | `src/engine.py` | 根除 D3 LLM 幻觉入库 |
| 删除/弃用 `NowcoderAdapter` 和 `HaitouAdapter` 的注册 | `src/engine.py` | 根除 D1/D2 假数据入库 |

### P1 多源扩展(预计 1-2 周): 垂直源 + 微信渠道

| 改动 | 文件 | 收益 |
|---|---|---|
| `NowcoderRealSource`(真实牛客网 API 抓取) | `src/adapters/nowcoder_real.py` | 校招日历/内推真实数据 |
| `YingjieshengSource`(应届生求职网) | `src/adapters/yingjiesheng_source.py` | 校招聚合数据 |
| `ShixisengSource`(实习僧) | `src/adapters/shixiseng_source.py` | 实习岗位 |
| `NcssSource`(国家大学生就业服务平台) | `src/adapters/ncss_source.py` | 政府权威渠道 |
| `WeChatRSSSource`(RSSHub 自建实例) | `src/adapters/wechat_rss_source.py` | **微信渠道主线落地** |
| RSSHub Docker 部署配置 | `docker-compose.yml` | 自建 RSSHub 实例 |
| 招聘类公众号订阅列表 | `data/wechat_feeds.json` | 微信内容源配置 |
| 匹配度评分模块(DeepSeek 评分器) | `src/adapters/job_aggregator.py` | 智能匹配度评分 |
| 删除旧的 `nowcoder.py`/`haitou.py`/`deepseek_adapter.py` | — | 清理技术债务 |
| 测试(单元测试 + 不变量测试 + 网络测试) | `tests/` | 回归保障 |

### P2 规模化(预计 2-4 周): 远程源 + 定时采集 + 高级特性

| 改动 | 文件 | 收益 |
|---|---|---|
| `EleduckSource`(电鸭社区远程岗位) | `src/adapters/eleduck_source.py` | 远程岗位补充 |
| 定时采集调度 | `src/scheduler.py` | 数据时效性 |
| 岗位过期标记(90 天) | `src/db.py` | 过期岗位降权 |
| `CompanyRegistry`(公司名归一化) | `src/registry/company_registry.py` | 公司名标准化 |
| 搜狗微信降级源 | `src/adapters/sogou_wechat_source.py` | 微信渠道降级链 |
| 增量缓存(避免重复 LLM 调用) | `src/db.py` | 降低 LLM 成本 |
| (可选)大厂全量 API 覆盖 | `src/adapters/bigtech_source.py` | 扩展至 10+ 大厂 |

---

## 6. 合规与风险

### 6.1 爬取招聘平台的法律边界

1. **《反不正当竞争法》第 12 条(互联网专条)**: 经营者不得利用技术手段, 通过影响用户选择或者其他方式, 妨碍、破坏其他经营者合法提供的网络产品或者服务正常运行。爬取招聘平台数据若用于商业竞争(如竞品分析、数据售卖), 可能触发此条。

2. **真实判例参考**:
   - Boss 直聘(华品招聘)诉某爬虫公司案: 北京海淀法院判决被告赔偿 50 万元并停止不正当竞争行为(2021 年) [需验证: 具体案号];
   - 大众点评诉百度案(2016): 上海知识产权法院判决百度因抓取大众点评用户点评信息赔偿 323 万元 — 确立了「实质性替代」判断标准 [需验证];
   - 微博诉脉脉案(2016): 北京知识产权法院确立「三重授权原则」(用户授权 + 平台授权 + 用户再授权) [需验证]。

3. **本项目合规策略**:
   - **不直爬高风险平台**(Boss 直聘/拉勾/猎聘等), 改用搜索 API 间接获取;
   - **大厂官网校招 API**: 公开展示的招聘信息, 正常频率(≤ 1 次/秒)抓取属于合理使用;
   - **政府/公共平台**: 公开信息, 遵守 robots.txt;
   - **不存储个人信息**: 仅存储公司名、岗位名、城市等公开商业信息, 不存储招聘联系人姓名、手机号等(《个人信息保护法》第 13 条)。

### 6.2 微信生态抓取的风控与合规

1. **账号风控**: 微信对自动化行为检测极严, 搜一搜自动化抓取可能导致微信账号被限制功能或封禁 [需验证]。这也是本报告不推荐 Playwright 方案的核心原因。

2. **《微信公众平台服务协议》**: 明确禁止未经授权的自动化采集; 但 RSSHub 通过第三方镜像站间接获取, 在法律上存在灰色地带 [需验证]。

3. **本项目合规策略**:
   - 使用 RSSHub 自建实例 + 第三方镜像站(非直连微信), 降低直接违反微信协议的风险;
   - 仅获取公众号文章标题、摘要等公开信息;
   - 保留原文链接并注明来源;
   - 不存储文章中的联系人个人信息。

### 6.3 LLM 幻觉治理

1. **结构性防线**(代码级不变量):
   - URL 溯源: `job.apply_url` 必须等于 `raw.url`, LLM 提取 Prompt 中**不包含 URL 字段**, URL 由系统回填;
   - 预过滤: 假 URL 模式(`example.com`, `{`, `}`)在管线入口即被拦截;
   - 指纹去重: 含 URL 的 4 元组指纹, 防止同一岗位多版本入库。

2. **LLM Prompt 约束**:
   - 提取 Prompt 明确要求「只提取文本中明确出现的信息, 不要推测或补充」;
   - 非招聘信息返回 `{"is_job_posting": false}` 跳过, 避免将无关内容误当岗位。

3. **兜底策略**:
   - LLM 调用失败时降级为直接映射(`_direct_map`), 仅使用原始数据中实际存在的字段;
   - 空结果返回诚实空态, 不触发兜底生成。

---

## 7. 与旧报告的增量关系

| 旧报告(research_job_sources.md)章节 | 本报告增量 |
|---|---|
| 第 1 节: 多大模型扩展 | **不重复**。本报告不重新对比 LLM, 仅重新定位 DeepSeek 为「提取与评分器」 |
| 第 2 节: 微信公众号招聘数据获取 | **增量深化**: 逐一评估 5 条路线的入口 URL、反爬、工程成本, 给出推荐主线与降级链 |
| 第 3 节: 官方网站与招聘平台 | **增量深化**: 新增 12 类数据源矩阵 + 总评对比表 + 法律风险引用 |
| 第 4 节: 架构设计 | **增量深化**: 对齐辅导员重构范式, 给出精确到文件的 P0/P1/P2 路线图 |
| 第 5 节: 总结与建议 | **增量深化**: 三阶段路线图替代原有的两阶段建议 |

---

## 8. 来源清单

### 源码文件(逐行阅读确认)
- `src/engine.py` — `MultiSourceJobEngine` 并发抓取与指纹去重逻辑
- `src/adapters/base.py` — `BaseJobSourceAdapter` 抽象基类与 MD5 指纹
- `src/adapters/deepseek_adapter.py` — DeepSeek 适配器(委托 `DeepSeekJobHunter`)
- `src/adapters/nowcoder.py` — 牛客网适配器(硬编码 3 条假数据)
- `src/adapters/haitou.py` — 海投网适配器(硬编码 2 条假数据)
- `src/deepseek_client.py` — `DeepSeekJobHunter`(LLM 生成 + Mock 模式)
- `src/models.py` — `JobItem`/`UserProfile`/`SearchResult` 模型定义
- `src/server.py` — `/api/search_jobs` API 入口
- `src/db.py` — SQLite 持久化与列迁移
- `src/adapters/counselor_aggregator.py` — 辅导员多源聚合器(架构范式参考)
- `src/adapters/counselor_base.py` — 辅导员数据源契约(架构范式参考)
- `tests/test_engine.py` — 引擎去重测试
- `tests/test_multi_adapters.py` — 多适配器测试

### 项目文档(已阅读引用)
- `docs/research_job_sources.md` — 旧版岗位数据多源获取调研
- `docs/design_counselor_engine_refactor.md` — 辅导员引擎重构方案(架构范式)
- `docs/research_counselor_expansion.md` — 辅导员数据源扩展调研(报告格式参考)

### 外部参考([需验证] — 未实时访问)
- 微信搜一搜: `https://search.weixin.qq.com` — 入口可用性
- 搜狗微信搜索: `https://weixin.sogou.com/` — 反爬现状
- RSSHub 微信路由文档: `https://docs.rsshub.app/routes/social-media#wei-xin` — 路由机制与限制
- 牛客网招聘频道: `https://www.nowcoder.com/jobs` — API 端点
- 应届生求职网: `https://www.yingjiesheng.com/` — 栏目结构
- 实习僧: `https://www.shixiseng.com/` — API 可用性
- 国家大学生就业服务平台: `https://www.ncss.cn/` — 岗位栏目
- 电鸭社区: `https://eleduck.com/` — API/RSS 可用性
- Tavily: `https://tavily.com` — 价格与 API 文档
- Exa.ai: `https://exa.ai` — 价格与 API 文档
- Serper: `https://serper.dev` — 价格与 API 文档
- SerpAPI: `https://serpapi.com` — 价格与 API 文档
- 传送门: `https://chuansongme.com` — 公众号镜像站可用性
- 微信年华: `https://wxnmh.com` — 公众号镜像站可用性

---

## 9. 在线核实补记(2026-07-29,主会话 WebFetch/WebSearch 复核)

报告撰写时子代理网络工具受限,以下关键条目由主会话补充在线核实:

| 条目 | 核实结果 |
|---|---|
| Serper 免费额度 | ✅ 已确认:注册送 2,500 次(一次性、6 个月有效、无需信用卡);付费约 $1/1000 次,量大低至 $0.3/1000 次;返回结构化 Google SERP JSON |
| Tavily 定位 | ✅ 已确认:面向 AI Agent 的实时搜索 API,返回清洗、结构化、分块后的网页内容(定价页需单独核实) |
| 搜狗微信 `weixin.sogou.com` | ✅ 已确认在线:首页主打「订阅号及文章内容独家收录,一搜即达」,降级链可用 |
| RSSHub 微信路由 | ⚠️ 部分修正:实际存在的路由为 `/wechat/csm/:id`(chuansongme 源)、`/wechat/wemp/:id`(wemp.app 源)、`/wechat/mp/msgalbum/:biz/:aid`(公众号合集)等;报告所述 `/wechat/mp/:id` 未获证实。微信路由「经常失效、需自建实例」的判断属实 |
| **微信主线方案修正** | 🔄 新发现:**WeWe-RSS**([cooderl/wewe-rss](https://github.com/cooderl/wewe-rss))基于微信读书接口、支持私有化部署,被少数派、腾讯云社区等多方推荐为比 RSSHub 微信路由更稳定的公众号订阅方案。微信主线建议调整为:**WeWe-RSS 自建 → RSSHub(csm/wemp 路由)→ 第三方聚合镜像站 → 搜狗微信(极低频)→ 空态** |

### 补充来源

- Serper 定价: [serper.dev](https://serper.dev/)、[Serper API 免费 Key 获取与使用指南](https://www.explinks.com/blog/ua-serper-api-free-key-guide/)、[2026 免费 Google Search API 横评](https://apiserpent.com/blog/free-google-search-api-tested)
- RSSHub 微信路由现状: [RSSHub 仓库 wechat 路由源码](https://github.com/DIYgod/RSSHub/blob/master/lib/routes/wechat/ce.ts)、[公众号支持 RSS 订阅(含 msgalbum 路由参数说明)](https://www.cnblogs.com/98record/p/gong-zhong-hao-zhi-chirss-ding-yue.html)、[RSSHub 文档国内镜像](https://rsshub-docs-mirror.github.io/zh/deploy/)
- WeWe-RSS: [cooderl/wewe-rss](https://github.com/cooderl/wewe-rss)、[少数派:WeWe RSS——更优雅的微信公众号订阅源](https://sspai.com/post/93845)
- 搜狗微信: [weixin.sogou.com](https://weixin.sogou.com/)
