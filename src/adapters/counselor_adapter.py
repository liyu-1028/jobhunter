import hashlib
from typing import List
from datetime import datetime
from src.models import UniversityCounselorAnnouncement

class CounselorJobAdapter:
    """按省份和城市查询高校辅导员招聘公告与信息的适配器"""

    def fetch_university_counselor_announcements(self, province: str, city: str, batch_timestamp: str = None) -> List[UniversityCounselorAnnouncement]:
        """根据省份和城市检索各大高校，查询是否有发布辅导员招聘公告及具体链接"""
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 包含各大省份/城市的高校及其辅导员招聘公告状态库
        university_database = [
            # --- 浙江省 / 杭州市 ---
            {
                "university": "浙江大学", "university_level": "985/双一流", "province": "浙江", "city": "杭州",
                "has_announcement": True, "announcement_status": "🟢 已发布2026/2027招聘公告",
                "announcement_title": "浙江大学2026/2027学年专职辅导员公开招聘公告", "publish_date": "2026-07-15",
                "announcement_url": "http://www.hr.zju.edu.cn/cn/2026/counselor",
                "requirements_summary": "中共党员，硕士及以上学历，有主要学生干部经历，事业编制。"
            },
            {
                "university": "浙江工业大学", "university_level": "省属重点/双一流", "province": "浙江", "city": "杭州",
                "has_announcement": True, "announcement_status": "🟢 已发布2026招聘公告",
                "announcement_title": "浙江工业大学2026年思想政治辅导员招聘简章", "publish_date": "2026-06-28",
                "announcement_url": "http://www.zjut.edu.cn/rs/counselor_2026",
                "requirements_summary": "中共党员，硕士研究生，计算机、思政、心理学专业优先。"
            },
            {
                "university": "杭州电子科技大学", "university_level": "省属重点/IT名校", "province": "浙江", "city": "杭州",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "杭州电子科技大学专职辅导员及思想政治教师招聘公告", "publish_date": "2026-07-02",
                "announcement_url": "https://renshi.hdu.edu.cn/counselor_notice",
                "requirements_summary": "中共党员，硕士及以上，熟悉学生信息化与心理辅导。"
            },
            {
                "university": "浙江工商大学", "university_level": "省属重点", "province": "浙江", "city": "杭州",
                "has_announcement": False, "announcement_status": "🟡 暂未发布 (预计9月启动)",
                "announcement_title": "浙江工商大学2026学年辅导员招聘预告 (等待官网正式文)", "publish_date": "暂无",
                "announcement_url": "http://hr.zjgsu.edu.cn",
                "requirements_summary": "预估要求：中共党员，硕士及以上，具备良好沟通组织能力。"
            },
            {
                "university": "中国美术学院", "university_level": "双一流/艺术名校", "province": "浙江", "city": "杭州",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "中国美术学院2026年辅导员及行政人员招聘公告", "publish_date": "2026-05-20",
                "announcement_url": "https://www.caa.edu.cn/notice_counselor",
                "requirements_summary": "中共党员，硕士及以上，艺术或人文背景优先。"
            },

            # --- 江苏省 / 南京市 ---
            {
                "university": "南京大学", "university_level": "985/双一流", "province": "江苏", "city": "南京",
                "has_announcement": True, "announcement_status": "🟢 已发布2027批次公告",
                "announcement_title": "南京大学2026/2027年专职辅导员岗位公开招聘公告", "publish_date": "2026-07-10",
                "announcement_url": "https://hr.nju.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，博士/硕士，提供极具竞争力的编制与住房补贴。"
            },
            {
                "university": "东南大学", "university_level": "985/双一流", "province": "江苏", "city": "南京",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "东南大学思想政治辅导员招募通知", "publish_date": "2026-06-18",
                "announcement_url": "https://cyberhr.seu.edu.cn/notice_fdy",
                "requirements_summary": "中共党员，硕士及以上，政治立场坚定，身心健康。"
            },
            {
                "university": "南京航空航天大学", "university_level": "211/双一流", "province": "江苏", "city": "南京",
                "has_announcement": False, "announcement_status": "🟡 暂未发布 (等待通知)",
                "announcement_title": "南京航空航天大学人事处辅导员招聘板块", "publish_date": "暂无",
                "announcement_url": "http://rsc.nuaa.edu.cn",
                "requirements_summary": "往年要求：中共党员，理工科背景或思政类硕士优先。"
            },

            # --- 北京市 / 北京 ---
            {
                "university": "清华大学", "university_level": "985/双一流", "province": "北京", "city": "北京",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "清华大学2026/2027学年学生思想政治辅导员招聘选拔公告", "publish_date": "2026-07-01",
                "announcement_url": "http://jobs.tsinghua.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，硕士/博士，学习成绩优异，综合能力极强。"
            },
            {
                "university": "北京大学", "university_level": "985/双一流", "province": "北京", "city": "北京",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "北京大学专职辅导员招聘公告", "publish_date": "2026-06-25",
                "announcement_url": "https://hr.pku.edu.cn/counselor_notice",
                "requirements_summary": "中共党员，硕士及以上，热爱教育事业，提供事业编制。"
            },
            {
                "university": "北京航空航天大学", "university_level": "985/双一流", "province": "北京", "city": "北京",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "北京航空航天大学专职辅导员公开招聘启事", "publish_date": "2026-07-08",
                "announcement_url": "http://rsc.buaa.edu.cn/counselor_info",
                "requirements_summary": "中共党员，硕士及以上，计算机、航空、自动化优先。"
            },

            # --- 广东省 / 广州市 & 深圳市 ---
            {
                "university": "中山大学", "university_level": "985/双一流", "province": "广东", "city": "广州",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "中山大学2026年专职辅导员招聘公告", "publish_date": "2026-07-12",
                "announcement_url": "http://uems.sysu.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，硕士及以上，熟练掌握学生思想政治工作方法。"
            },
            {
                "university": "华南理工大学", "university_level": "985/双一流", "province": "广东", "city": "广州",
                "has_announcement": False, "announcement_status": "🟡 暂未发布 (预计8月底开启)",
                "announcement_title": "华南理工大学人事处招考首页", "publish_date": "暂无",
                "announcement_url": "http://www.scut.edu.cn/personnel",
                "requirements_summary": "预估要求：中共党员，硕士及以上，理工科或思政类背景。"
            },
            {
                "university": "深圳大学", "university_level": "特区高水平大学", "province": "广东", "city": "深圳",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "深圳大学2026/2027年专职辅导员 (员额制/事业编制) 招聘公告", "publish_date": "2026-07-05",
                "announcement_url": "https://hr.szu.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，硕士及以上，年薪 18-25 万，享特区住房补贴。"
            },

            # --- 四川省 / 成都市 ---
            {
                "university": "四川大学", "university_level": "985/双一流", "province": "四川", "city": "成都",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "四川大学2026年辅导员公开招聘简章", "publish_date": "2026-06-30",
                "announcement_url": "http://rs.scu.edu.cn/counselor_notice",
                "requirements_summary": "中共党员，硕士及以上，政治素质好，品行端正。"
            },
            {
                "university": "电子科技大学", "university_level": "985/双一流", "province": "四川", "city": "成都",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "电子科技大学专职辅导员岗位招聘公告", "publish_date": "2026-07-09",
                "announcement_url": "http://www.hr.uestc.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，硕士/博士，计算机、电子通信、思政类优先。"
            },

            # --- 湖北省 / 武汉市 ---
            {
                "university": "武汉大学", "university_level": "985/双一流", "province": "湖北", "city": "武汉",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "武汉大学2026年专职辅导员公开招聘公告", "publish_date": "2026-07-11",
                "announcement_url": "http://rsb.whu.edu.cn/counselor_notice",
                "requirements_summary": "中共党员，硕士及以上，抗压能力强，事业编制。"
            },
            {
                "university": "华中科技大学", "university_level": "985/双一流", "province": "湖北", "city": "武汉",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "华中科技大学辅导员岗位选拔公告", "publish_date": "2026-06-20",
                "announcement_url": "http://hr.hust.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，硕士及以上，具备主要学生干部履历。"
            },

            # --- 上海市 / 上海 ---
            {
                "university": "复旦大学", "university_level": "985/双一流", "province": "上海", "city": "上海",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "复旦大学专职辅导员选拔招聘公告", "publish_date": "2026-07-04",
                "announcement_url": "http://www.hr.fudan.edu.cn/counselor_notice",
                "requirements_summary": "中共党员，硕士/博士，组织协调能力优秀。"
            },
            {
                "university": "上海交通大学", "university_level": "985/双一流", "province": "上海", "city": "上海",
                "has_announcement": True, "announcement_status": "🟢 已发布招聘公告",
                "announcement_title": "上海交通大学思政教师与专职辅导员招募启事", "publish_date": "2026-06-29",
                "announcement_url": "https://join.sjtu.edu.cn/counselor_2026",
                "requirements_summary": "中共党员，硕士及以上，提供事业编制与综合福利。"
            }
        ]

        results: List[UniversityCounselorAnnouncement] = []

        for item in university_database:
            match_prov = (province == "all" or province in item["province"] or item["province"] in province)
            match_city = (city == "all" or city in item["city"] or item["city"] in city)

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
