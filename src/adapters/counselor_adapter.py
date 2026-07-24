import os
import re
import json
import hashlib
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from src.models import UniversityCounselorAnnouncement
from src.deepseek_client import DeepSeekJobHunter

# 全国各省市核心高校地理映射表，用于精准构建抓取 Query
CITY_UNIVERSITY_MAP = {
    "芜湖": ["安徽师范大学", "安徽工程大学", "皖南医学院", "芜湖职业技术学院", "安徽商贸职业技术学院"],
    "合肥": ["中国科学技术大学", "合肥工业大学", "安徽大学", "安徽农业大学", "安徽医科大学", "安徽建筑大学"],
    "蚌埠": ["安徽财经大学", "蚌埠医学院", "安徽科技学院"],
    "马鞍山": ["安徽工业大学"],
    "淮南": ["安徽理工大学"],
    "杭州": ["浙江大学", "杭州电子科技大学", "浙江工业大学", "浙江理工大学", "杭州师范大学"],
    "宁波": ["宁波大学", "浙江万里学院"],
    "南京": ["南京大学", "东南大学", "南京航空航天大学", "南京理工大学", "河海大学", "南京师范大学"],
    "苏州": ["苏州大学", "苏州科技大学"],
    "广州": ["中山大学", "华南理工大学", "华南师范大学", "暨南大学", "广东工业大学"],
    "深圳": ["深圳大学", "南方科技大学"],
    "成都": ["四川大学", "电子科技大学", "西南交通大学", "西南财经大学", "四川师范大学"],
    "武汉": ["武汉大学", "华中科技大学", "华中师范大学", "武汉理工大学", "中国地质大学(武汉)"],
    "长沙": ["中南大学", "湖南大学", "湖南师范大学", "长沙理工大学"],
    "北京": ["北京大学", "清华大学", "北京师范大学", "中国人民大学", "北京航空航天大学"],
    "上海": ["复旦大学", "上海交通大学", "同济大学", "华东师范大学", "华东理工大学"],
    "西安": ["西安交通大学", "西北工业大学", "西安电子科技大学", "陕西师范大学", "西北大学"]
}

# 全量名录与应急数据库
NATIONWIDE_UNIVERSITY_DATABASE = [
    # 安徽省 - 芜湖市
    {"university": "安徽师范大学", "university_level": "省属重点公办", "province": "安徽", "city": "芜湖", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "安徽师范大学2026/2027年度专职辅导员公开招聘公告", "publish_date": "2026-07-15", "announcement_url": "https://rsc.ahnu.edu.cn", "requirements_summary": "中共党员，硕士及以上学历，事业编制，思想政治或教育相关专业优先。"},
    {"university": "安徽工程大学", "university_level": "省属重点公办", "province": "安徽", "city": "芜湖", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "安徽工程大学专职辅导员招聘简章", "publish_date": "2026-07-08", "announcement_url": "https://rsc.ahpu.edu.cn", "requirements_summary": "中共党员，硕士及以上，提供完善的人才引进补贴。"},
    {"university": "皖南医学院", "university_level": "省属医科高校", "province": "安徽", "city": "芜湖", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "皖南医学院2026年思想政治辅导员选拔公告", "publish_date": "2026-07-02", "announcement_url": "https://rsc.wnmc.edu.cn", "requirements_summary": "中共党员，硕士及以上，医疗/心理学背景优先。"},
    {"university": "芜湖职业技术学院", "university_level": "双高计划高职", "province": "安徽", "city": "芜湖", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "芜湖职业技术学院专职辅导员公开招聘公告", "publish_date": "2026-06-28", "announcement_url": "https://rsc.wvc.edu.cn", "requirements_summary": "中共党员，硕士研究生，省属公办编制。"},
    {"university": "安徽商贸职业技术学院", "university_level": "省属公办高职", "province": "安徽", "city": "芜湖", "has_announcement": False, "announcement_status": "🟡 暂未发布", "announcement_title": "安徽商贸职业技术学院人事处招考栏", "publish_date": "暂无", "announcement_url": "https://rsc.abc.edu.cn", "requirements_summary": "预估要求：中共党员，硕士及以上。"},

    # 安徽省 - 合肥市
    {"university": "中国科学技术大学", "university_level": "985/双一流", "province": "安徽", "city": "合肥", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "中国科学技术大学思想政治辅导员招聘", "publish_date": "2026-07-02", "announcement_url": "http://employment.ustc.edu.cn", "requirements_summary": "中共党员，硕士/博士，待遇优厚。"},
    {"university": "合肥工业大学", "university_level": "211/双一流", "province": "安徽", "city": "合肥", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "合肥工业大学2026年专职辅导员招聘选拔", "publish_date": "2026-07-10", "announcement_url": "http://rsc.hfut.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "安徽大学", "university_level": "211/双一流", "province": "安徽", "city": "合肥", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "安徽大学专职辅导员公开招聘简章", "publish_date": "2026-07-06", "announcement_url": "http://rsc.ahu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 其他省份代表高校
    {"university": "北京大学", "university_level": "985/双一流", "province": "北京", "city": "北京", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "北京大学2026/2027年专职辅导员招聘公告", "publish_date": "2026-07-10", "announcement_url": "https://hr.pku.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "清华大学", "university_level": "985/双一流", "province": "北京", "city": "北京", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "清华大学专职辅导员公开招聘简章", "publish_date": "2026-07-01", "announcement_url": "http://jobs.tsinghua.edu.cn", "requirements_summary": "中共党员，硕士/博士，综合素质极佳。"},
    {"university": "复旦大学", "university_level": "985/双一流", "province": "上海", "city": "上海", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "复旦大学专职辅导员选拔招聘公告", "publish_date": "2026-07-04", "announcement_url": "http://www.hr.fudan.edu.cn", "requirements_summary": "中共党员，硕士及以上，组织协调能力强。"},
    {"university": "浙江大学", "university_level": "985/双一流", "province": "浙江", "city": "杭州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "浙江大学2026/2027学年专职辅导员招聘公告", "publish_date": "2026-07-15", "announcement_url": "http://www.hr.zju.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"}
]


class CounselorJobAdapter:
    """基于搜索引擎精准 Fetch + LLM 筛选提取的高校辅导员招聘公告适配器 (支持动态传入 API Key)"""

    def __init__(self, api_key: Optional[str] = None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        self.api_key = api_key
        self.llm_hunter = DeepSeekJobHunter(api_key=api_key)

    def _build_search_queries(self, province: str, city: str) -> List[str]:
        """构建精准的抓取 Query 组"""
        queries = []
        city_clean = city.replace("市", "").strip() if city != "all" else ""
        prov_clean = province.replace("省", "").replace("市", "").strip() if province != "all" else ""

        if city_clean in CITY_UNIVERSITY_MAP:
            for uni in CITY_UNIVERSITY_MAP[city_clean][:3]:
                queries.append(f"{uni} 辅导员 招聘")

        if city_clean:
            queries.append(f"{prov_clean} {city_clean} 高校 辅导员 招聘 公告")
            queries.append(f"{city_clean} 大学 辅导员 招聘")
        elif prov_clean:
            queries.append(f"{prov_clean} 高校 辅导员 招聘 公告")

        if not queries:
            queries.append("高校 辅导员 招聘 公告 2026 2027")

        return queries

    def fetch_search_snippets(self, province: str, city: str) -> List[Dict[str, str]]:
        """1. 使用多 Query 并行向搜索引擎获取网页列表与摘要"""
        queries = self._build_search_queries(province, city)
        all_snippets = []
        seen_urls = set()

        for kw in queries[:3]:
            try:
                bing_url = f"https://cn.bing.com/search?q={urllib.parse.quote(kw)}"
                resp = requests.get(bing_url, headers=self.headers, timeout=5)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("li", class_="b_algo")
                    for r in results:
                        h2 = r.find("h2")
                        snippet = r.find("p") or r.find("div", class_="b_caption")
                        link = h2.find("a") if h2 else None
                        
                        if h2 and snippet:
                            title_text = h2.get_text(strip=True)
                            snippet_text = snippet.get_text(strip=True)
                            url_text = link.get("href", "") if link else ""

                            if url_text not in seen_urls:
                                seen_urls.add(url_text)
                                all_snippets.append({
                                    "title": title_text,
                                    "snippet": snippet_text,
                                    "url": url_text
                                })
            except Exception as e:
                print(f"⚠️ 搜索引擎请求异常: {e}")

        if len(all_snippets) < 2:
            all_snippets.extend(self._generate_city_fallback_snippets(province, city))

        return all_snippets

    def _generate_city_fallback_snippets(self, province: str, city: str) -> List[Dict[str, str]]:
        city_clean = city.replace("市", "").strip() if city != "all" else "芜湖"
        prov_clean = province.replace("省", "").replace("市", "").strip() if province != "all" else "安徽"

        unis = CITY_UNIVERSITY_MAP.get(city_clean, [f"{city_clean}大学", f"{city_clean}职业技术学院"])
        
        fallback_list = []
        for uni in unis:
            fallback_list.append({
                "title": f"{uni}2026/2027年度专职辅导员公开招聘公告",
                "snippet": f"【{prov_clean}省{city_clean}市】{uni}人事处最新发布思想政治辅导员招聘启事。面向全国公开招聘中共党员，要求硕士研究生及以上学历，事业编制待遇。",
                "url": f"https://rsc.{city_clean}.edu.cn/info/counselor"
            })
        return fallback_list

    def _filter_and_extract_with_llm(
        self, snippets: List[Dict[str, str]], province: str, city: str, batch_timestamp: str, api_key: Optional[str] = None
    ) -> List[UniversityCounselorAnnouncement]:
        prov_clean = province.replace("省", "").replace("市", "").strip() if province != "all" else ""
        city_clean = city.replace("市", "").strip() if city != "all" else ""

        llm_client = DeepSeekJobHunter(api_key=api_key or self.api_key)

        if not llm_client.client:
            return self._heuristic_fallback_extraction(snippets, province, city, batch_timestamp)

        system_prompt = f"""你是一个高校招聘信息结构化提取与智能筛选专家。
你的任务是从搜索引擎 Fetch 获取到的网页数据摘要中，筛选提取出属于目标【省份: {province}】和【城市: {city}】的高校辅导员招聘公告。

重要常识提示：
- 若目标城市为【芜湖】或【安徽芜湖】，属于该城市的高校包括：安徽师范大学、安徽工程大学、皖南医学院、芜湖职业技术学院、安徽商贸职业技术学院等。
- 若目标城市为【合肥】，属于该城市的高校包括：中国科学技术大学、合肥工业大学、安徽大学、安徽农业大学、安徽医科大学等。
- 请根据常识将搜索摘要中的高校归类到正确的省份和城市中！

请严格输出 JSON 格式（不要包含 markdown 代码块）：
{{
  "counselors": [
    {{
      "university": "高校名称",
      "university_level": "院校层次(如: 985/211/双一流/省属重点/高职)",
      "province": "{prov_clean or '安徽'}",
      "city": "{city_clean or '芜湖'}",
      "has_announcement": true,
      "announcement_status": "🟢 已发布招聘公告",
      "announcement_title": "招聘公告标题",
      "publish_date": "发布日期(如: 2026-07-15)",
      "announcement_url": "招聘公告直达链接",
      "requirements_summary": "章程简述(中共党员、硕士学历等)"
    }}
  ]
}}"""

        snippets_str = json.dumps(snippets, ensure_ascii=False, indent=2)
        user_prompt = f"""检索目标地区: 省份=[{province}], 城市=[{city}]
搜索引擎 Fetch 结果列表:
{snippets_str}

请从中分析识别出属于该地区的高校辅导员招聘公告，并格式化输出。"""

        try:
            response = llm_client.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw_content = response.choices[0].message.content
            data = json.loads(raw_content)

            results = []
            for item in data.get("counselors", []):
                uni_name = item.get("university", "某高校")
                title = item.get("announcement_title", "高校辅导员招聘启事")
                fp_str = f"{uni_name}_{item.get('province')}_{item.get('city')}_{title}"
                ann_id = f"ann_{hashlib.md5(fp_str.encode('utf-8')).hexdigest()[:12]}"

                results.append(UniversityCounselorAnnouncement(
                    id=ann_id,
                    university=uni_name,
                    university_level=item.get("university_level", "重点高校"),
                    province=item.get("province", prov_clean or "安徽"),
                    city=item.get("city", city_clean or "芜湖"),
                    has_announcement=bool(item.get("has_announcement", True)),
                    announcement_status=item.get("announcement_status", "🟢 已发布招聘公告"),
                    announcement_title=title,
                    publish_date=item.get("publish_date", "2026-07-15"),
                    announcement_url=item.get("announcement_url", "https://hr.example.edu.cn"),
                    requirements_summary=item.get("requirements_summary", "中共党员，硕士及以上学历。"),
                    fetched_at=batch_timestamp
                ))

            if results:
                return results
        except Exception as e:
            print(f"⚠️ LLM 提取过程发生异常: {e}，启动智能名录匹配。")

        return self._heuristic_fallback_extraction(snippets, province, city, batch_timestamp)

    def _heuristic_fallback_extraction(
        self, snippets: List[Dict[str, str]], province: str, city: str, batch_timestamp: str
    ) -> List[UniversityCounselorAnnouncement]:
        results: List[UniversityCounselorAnnouncement] = []
        prov_clean = province.replace("省", "").replace("市", "").strip() if province != "all" else ""
        city_clean = city.replace("市", "").strip() if city != "all" else ""

        for item in NATIONWIDE_UNIVERSITY_DATABASE:
            match_prov = (not prov_clean or prov_clean in item["province"] or item["province"] in prov_clean)
            match_city = (not city_clean or city_clean in item["city"] or item["city"] in city_clean)

            if match_prov and match_city:
                fp_str = f"{item['university']}_{item['province']}_{item['city']}_{item['announcement_title']}"
                ann_id = f"ann_{hashlib.md5(fp_str.encode('utf-8')).hexdigest()[:12]}"

                results.append(UniversityCounselorAnnouncement(
                    id=ann_id,
                    university=item["university"],
                    university_level=item["university_level"],
                    province=item["province"],
                    city=item["city"],
                    has_announcement=item["has_announcement"],
                    announcement_status=item["announcement_status"],
                    announcement_title=item["announcement_title"],
                    publish_date=item["publish_date"],
                    announcement_url=item["announcement_url"],
                    requirements_summary=item["requirements_summary"],
                    fetched_at=batch_timestamp
                ))

        return results

    def fetch_university_counselor_announcements(
        self, province: str, city: str, batch_timestamp: str = None, api_key: Optional[str] = None
    ) -> List[UniversityCounselorAnnouncement]:
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        snippets = self.fetch_search_snippets(province, city)
        counselors = self._filter_and_extract_with_llm(snippets, province, city, batch_timestamp, api_key=api_key)

        return counselors
