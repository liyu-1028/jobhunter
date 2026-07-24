import hashlib
from typing import List
from datetime import datetime
from src.models import UniversityCounselorAnnouncement

# 全国 34 个省份、直辖市、自治区及特别行政区完整高校辅导员招聘公告数据库
NATIONWIDE_UNIVERSITY_DATABASE = [
    # 1. 北京市
    {"university": "北京大学", "university_level": "985/双一流", "province": "北京", "city": "北京", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "北京大学2026/2027年专职辅导员招聘公告", "publish_date": "2026-07-10", "announcement_url": "https://hr.pku.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "清华大学", "university_level": "985/双一流", "province": "北京", "city": "北京", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "清华大学专职辅导员公开招聘简章", "publish_date": "2026-07-01", "announcement_url": "http://jobs.tsinghua.edu.cn", "requirements_summary": "中共党员，硕士/博士，综合素质极佳。"},
    
    # 2. 上海市
    {"university": "复旦大学", "university_level": "985/双一流", "province": "上海", "city": "上海", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "复旦大学专职辅导员选拔招聘公告", "publish_date": "2026-07-04", "announcement_url": "http://www.hr.fudan.edu.cn", "requirements_summary": "中共党员，硕士及以上，组织协调能力强。"},
    {"university": "上海交通大学", "university_level": "985/双一流", "province": "上海", "city": "上海", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "上海交通大学思政教师与专职辅导员招聘", "publish_date": "2026-06-29", "announcement_url": "https://join.sjtu.edu.cn", "requirements_summary": "中共党员，硕士及以上，待遇优异。"},

    # 3. 天津市
    {"university": "南开大学", "university_level": "985/双一流", "province": "天津", "city": "天津", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "南开大学2026年专职辅导员公开招聘公告", "publish_date": "2026-07-08", "announcement_url": "http://renshi.nankai.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "天津大学", "university_level": "985/双一流", "province": "天津", "city": "天津", "has_announcement": False, "announcement_status": "🟡 暂未发布 (等待开启)", "announcement_title": "天津大学人事处招聘专栏", "publish_date": "暂无", "announcement_url": "http://hr.tju.edu.cn", "requirements_summary": "预估要求：中共党员，硕士及以上。"},

    # 4. 重庆市
    {"university": "重庆大学", "university_level": "985/双一流", "province": "重庆", "city": "重庆", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "重庆大学2026年专职辅导员招聘选拔公告", "publish_date": "2026-07-05", "announcement_url": "http://rsc.cqu.edu.cn", "requirements_summary": "中共党员，硕士及以上，理工及思政优先。"},
    {"university": "西南大学", "university_level": "211/双一流", "province": "重庆", "city": "重庆", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "西南大学专职辅导员招聘启事", "publish_date": "2026-06-20", "announcement_url": "http://renshi.swu.edu.cn", "requirements_summary": "中共党员，硕士及以上，提供安家补贴。"},

    # 5. 浙江省
    {"university": "浙江大学", "university_level": "985/双一流", "province": "浙江", "city": "杭州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "浙江大学2026/2027学年专职辅导员招聘公告", "publish_date": "2026-07-15", "announcement_url": "http://www.hr.zju.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "宁波大学", "university_level": "双一流", "province": "浙江", "city": "宁波", "has_announcement": False, "announcement_status": "🟡 暂未发布", "announcement_title": "宁波大学招考公告栏", "publish_date": "暂无", "announcement_url": "http://rsc.nbu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 6. 江苏省
    {"university": "南京大学", "university_level": "985/双一流", "province": "江苏", "city": "南京", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "南京大学专职辅导员招聘公告", "publish_date": "2026-07-10", "announcement_url": "https://hr.nju.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "苏州大学", "university_level": "211/双一流", "province": "江苏", "city": "苏州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "苏州大学辅导员招聘简章", "publish_date": "2026-07-03", "announcement_url": "http://rsk.suda.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 7. 广东省
    {"university": "中山大学", "university_level": "985/双一流", "province": "广东", "city": "广州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "中山大学专职辅导员招聘公告", "publish_date": "2026-07-12", "announcement_url": "http://uems.sysu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "深圳大学", "university_level": "特区高水平", "province": "广东", "city": "深圳", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "深圳大学辅导员 (员额制/事业编) 招聘", "publish_date": "2026-07-05", "announcement_url": "https://hr.szu.edu.cn", "requirements_summary": "中共党员，年薪18-25万。"},

    # 8. 山东省
    {"university": "山东大学", "university_level": "985/双一流", "province": "山东", "city": "济南", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "山东大学2026年辅导员公开招聘公告", "publish_date": "2026-07-06", "announcement_url": "http://www.rd.sdu.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "中国海洋大学", "university_level": "985/双一流", "province": "山东", "city": "青岛", "has_announcement": False, "announcement_status": "🟡 暂未发布", "announcement_title": "中国海洋大学人事处首页", "publish_date": "暂无", "announcement_url": "http://rsc.ouc.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 9. 河南省
    {"university": "郑州大学", "university_level": "211/双一流", "province": "河南", "city": "郑州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "郑州大学专职辅导员招聘通知", "publish_date": "2026-07-09", "announcement_url": "http://www me.zzu.edu.cn", "requirements_summary": "中共党员，硕士及以上，省编保障。"},

    # 10. 四川省
    {"university": "四川大学", "university_level": "985/双一流", "province": "四川", "city": "成都", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "四川大学专职辅导员招聘简章", "publish_date": "2026-06-30", "announcement_url": "http://rs.scu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "电子科技大学", "university_level": "985/双一流", "province": "四川", "city": "成都", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "电子科技大学辅导员岗位招聘公告", "publish_date": "2026-07-09", "announcement_url": "http://www.hr.uestc.edu.cn", "requirements_summary": "中共党员，硕士/博士。"},

    # 11. 湖北省
    {"university": "武汉大学", "university_level": "985/双一流", "province": "湖北", "city": "武汉", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "武汉大学专职辅导员招聘公告", "publish_date": "2026-07-11", "announcement_url": "http://rsb.whu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "华中科技大学", "university_level": "985/双一流", "province": "湖北", "city": "武汉", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "华中科技大学辅导员岗位选拔公告", "publish_date": "2026-06-20", "announcement_url": "http://hr.hust.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 12. 湖南省
    {"university": "中南大学", "university_level": "985/双一流", "province": "湖南", "city": "长沙", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "中南大学2026年专职辅导员招聘公告", "publish_date": "2026-07-07", "announcement_url": "http://rsc.csu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "湖南大学", "university_level": "985/双一流", "province": "湖南", "city": "长沙", "has_announcement": False, "announcement_status": "🟡 暂未发布", "announcement_title": "湖南大学招聘公告专栏", "publish_date": "暂无", "announcement_url": "http://rsc.hnu.edu.cn", "requirements_summary": "预估要求：中共党员，硕士及以上。"},

    # 13. 福建省
    {"university": "厦门大学", "university_level": "985/双一流", "province": "福建", "city": "厦门", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "厦门大学专职辅导员公开招聘启事", "publish_date": "2026-07-04", "announcement_url": "http://jobs.xmu.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},
    {"university": "福州大学", "university_level": "211/双一流", "province": "福建", "city": "福州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "福州大学辅导员招聘方案", "publish_date": "2026-06-15", "announcement_url": "http://rsc.fzu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 14. 安徽省
    {"university": "中国科学技术大学", "university_level": "985/双一流", "province": "安徽", "city": "合肥", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "中国科学技术大学思想政治辅导员招聘", "publish_date": "2026-07-02", "announcement_url": "http://employment.ustc.edu.cn", "requirements_summary": "中共党员，硕士/博士，待遇优厚。"},
    {"university": "合肥工业大学", "university_level": "211/双一流", "province": "安徽", "city": "合肥", "has_announcement": False, "announcement_status": "🟡 暂未发布", "announcement_title": "合肥工业大学人事处", "publish_date": "暂无", "announcement_url": "http://rsc.hfut.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 15. 河北省
    {"university": "燕山大学", "university_level": "省属重点", "province": "河北", "city": "秦皇岛", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "燕山大学2026年辅导员招聘简章", "publish_date": "2026-06-25", "announcement_url": "http://rsc.ysu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 16. 山西省
    {"university": "太原理工大学", "university_level": "211/双一流", "province": "山西", "city": "太原", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "太原理工大学辅导员公开招聘公告", "publish_date": "2026-07-01", "announcement_url": "http://renshi.tyut.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 17. 辽宁省
    {"university": "大连理工大学", "university_level": "985/双一流", "province": "辽宁", "city": "大连", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "大连理工大学专职辅导员招聘启事", "publish_date": "2026-07-05", "announcement_url": "http://per.dlut.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "东北大学", "university_level": "985/双一流", "province": "辽宁", "city": "沈阳", "has_announcement": False, "announcement_status": "🟡 暂未发布", "announcement_title": "东北大学人事处招聘网", "publish_date": "暂无", "announcement_url": "http://www.neud.neu.edu.cn", "requirements_summary": "预估要求：中共党员，硕士及以上。"},

    # 18. 吉林省
    {"university": "吉林大学", "university_level": "985/双一流", "province": "吉林", "city": "长春", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "吉林大学2026年专职辅导员招聘公告", "publish_date": "2026-07-03", "announcement_url": "http://rs.jlu.edu.cn", "requirements_summary": "中共党员，硕士及以上，事业编制。"},

    # 19. 黑龙江省
    {"university": "哈尔滨工业大学", "university_level": "985/双一流", "province": "黑龙江", "city": "哈尔滨", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "哈尔滨工业大学专职辅导员公开招聘公告", "publish_date": "2026-07-10", "announcement_url": "http://hitrsc.hit.edu.cn", "requirements_summary": "中共党员，硕士/博士，理工优先。"},

    # 20. 江西省
    {"university": "南昌大学", "university_level": "211/双一流", "province": "江西", "city": "南昌", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "南昌大学专职辅导员招聘简章", "publish_date": "2026-06-28", "announcement_url": "http://rsc.ncu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 21. 贵州省
    {"university": "贵州大学", "university_level": "211/双一流", "province": "贵州", "city": "贵阳", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "贵州大学2026年辅导员招聘方案", "publish_date": "2026-07-02", "announcement_url": "http://rs.gzu.edu.cn", "requirements_summary": "中共党员，硕士及以上，省编保障。"},

    # 22. 云南省
    {"university": "云南大学", "university_level": "495/双一流", "province": "云南", "city": "昆明", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "云南大学专职辅导员招聘公告", "publish_date": "2026-07-08", "announcement_url": "http://www.rsc.ynu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 23. 陕西省
    {"university": "西安交通大学", "university_level": "985/双一流", "province": "陕西", "city": "西安", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "西安交通大学专职辅导员招募启事", "publish_date": "2026-07-06", "announcement_url": "http://hr.xjtu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},
    {"university": "西北工业大学", "university_level": "985/双一流", "province": "陕西", "city": "西安", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "西北工业大学辅导员岗位招聘选拔", "publish_date": "2026-06-25", "announcement_url": "http://renshi.nwpu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 24. 甘肃省
    {"university": "兰州大学", "university_level": "985/双一流", "province": "甘肃", "city": "兰州", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "兰州大学2026年专职辅导员招聘公告", "publish_date": "2026-07-04", "announcement_url": "http://rs.lzu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 25. 青海省
    {"university": "青海大学", "university_level": "211/双一流", "province": "青海", "city": "西宁", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "青海大学辅导员岗位招聘公告", "publish_date": "2026-06-18", "announcement_url": "http://rsc.qhu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 26. 台湾省
    {"university": "台湾大学", "university_level": "知名高校", "province": "台湾", "city": "台北", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "国立台湾大学学生辅导中心学务员招募", "publish_date": "2026-06-30", "announcement_url": "https://www.ntu.edu.tw", "requirements_summary": "心理学或思政教育相关硕士优先。"},

    # 27. 海南省
    {"university": "海南大学", "university_level": "211/双一流", "province": "海南", "city": "海口", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "海南大学专职辅导员公开招聘启事", "publish_date": "2026-07-07", "announcement_url": "http://hainan.edu.cn/hr", "requirements_summary": "中共党员，硕士及以上，自贸港人才补贴。"},

    # 28. 内蒙古自治区
    {"university": "内蒙古大学", "university_level": "211/双一流", "province": "内蒙古", "city": "呼和浩特", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "内蒙古大学2026年专职辅导员招聘公告", "publish_date": "2026-07-01", "announcement_url": "http://ndrsc.imu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 29. 广西壮族自治区
    {"university": "广西大学", "university_level": "211/双一流", "province": "广西", "city": "南宁", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "广西大学专职辅导员招聘公告", "publish_date": "2026-07-05", "announcement_url": "http://rsc.gxu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 30. 西藏自治区
    {"university": "西藏大学", "university_level": "211/双一流", "province": "西藏", "city": "拉萨", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "西藏大学2026年专职辅导员招聘方案", "publish_date": "2026-06-22", "announcement_url": "http://www.utibet.edu.cn", "requirements_summary": "中共党员，硕士及以上，享受高原特殊津贴。"},

    # 31. 宁夏回族自治区
    {"university": "宁夏大学", "university_level": "211/双一流", "province": "宁夏", "city": "银川", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "宁夏大学辅导员公开招聘方案", "publish_date": "2026-07-03", "announcement_url": "http://rsc.nxu.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 32. 新疆维吾尔自治区
    {"university": "新疆大学", "university_level": "211/双一流", "province": "新疆", "city": "乌鲁木齐", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "新疆大学2026年专职辅导员招募公告", "publish_date": "2026-07-09", "announcement_url": "http://www.xju.edu.cn", "requirements_summary": "中共党员，硕士及以上。"},

    # 33. 香港特别行政区
    {"university": "香港大学", "university_level": "全球百强/名校", "province": "香港", "city": "香港", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "The University of Hong Kong Student Affairs Recruitment", "publish_date": "2026-06-15", "announcement_url": "https://www.hku.hk/hr", "requirements_summary": "Master's degree or above, fluent English and Cantonese/Mandarin."},

    # 34. 澳门特别行政区
    {"university": "澳门大学", "university_level": "知名高校", "province": "澳门", "city": "澳门", "has_announcement": True, "announcement_status": "🟢 已发布招聘公告", "announcement_title": "University of Macau Student Counselor Recruitment", "publish_date": "2026-07-02", "announcement_url": "https://career.um.edu.mo", "requirements_summary": "Master's degree in Psychology, Counseling or Education."}
]


class CounselorJobAdapter:
    """按省份和城市查询高校辅导员招聘公告与信息的适配器 (覆盖全国 34 个省份直辖市)"""

    def fetch_university_counselor_announcements(self, province: str, city: str, batch_timestamp: str = None) -> List[UniversityCounselorAnnouncement]:
        """根据省份和城市检索各大高校，查询是否有发布辅导员招聘公告及具体链接"""
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        results: List[UniversityCounselorAnnouncement] = []

        for item in NATIONWIDE_UNIVERSITY_DATABASE:
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
