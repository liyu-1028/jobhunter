import hashlib
from typing import List
from datetime import datetime
from src.models import CounselorJobItem

class CounselorJobAdapter:
    """按省份和城市检索高校辅导员招聘信息的适配器"""

    def fetch_counselor_jobs(self, province: str, city: str, batch_timestamp: str = None) -> List[CounselorJobItem]:
        """根据省份和城市抓取高校辅导员招聘数据，分配统一批次时间戳"""
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 示例知识库与生成逻辑（涵盖全国重点高校及区域省市辅导员岗）
        counselor_data_pool = [
            # 浙江省 / 杭州市
            {
                "province": "浙江", "city": "杭州", "university": "浙江大学",
                "title": "2026/2027年专职辅导员 (事业编制)", "establishment_type": "事业编制", "salary": "12-18万/年",
                "requirements": ["中共党员 (含预备)", "硕士及以上学历", "有主要学生干部经历", "年龄30周岁以下"],
                "apply_url": "http://www.hr.zju.edu.cn", "status": "🟢 已开启报名"
            },
            {
                "province": "浙江", "city": "杭州", "university": "浙江工业大学",
                "title": "专职辅导员招聘公告", "establishment_type": "事业编制", "salary": "10-15万/年",
                "requirements": ["中共党员", "硕士研究生", "思想政治、计算机、管理专业优先"],
                "apply_url": "http://www.zjut.edu.cn", "status": "🟢 招聘中"
            },
            {
                "province": "浙江", "city": "杭州", "university": "杭州电子科技大学",
                "title": "专职辅导员与思想政治教育岗", "establishment_type": "事业编制", "salary": "11-16万/年",
                "requirements": ["中共党员", "硕士以上", "具备良好心理素质与沟通协调能力"],
                "apply_url": "https://renshi.hdu.edu.cn", "status": "🟡 预公告"
            },

            # 江苏省 / 南京市
            {
                "province": "江苏", "city": "南京", "university": "南京大学",
                "title": "专职辅导员公开招聘", "establishment_type": "事业编制", "salary": "13-20万/年",
                "requirements": ["中共党员", "博士/硕士", "具备高等教育管理经验优先"],
                "apply_url": "https://hr.nju.edu.cn", "status": "🟢 已开启报名"
            },
            {
                "province": "江苏", "city": "南京", "university": "东南大学",
                "title": "2026/2027辅导员招聘计划", "establishment_type": "事业编制", "salary": "12-18万/年",
                "requirements": ["中共党员", "硕士及以上", "政治立场坚定，身心健康"],
                "apply_url": "https://cyberhr.seu.edu.cn", "status": "🟢 已开启报名"
            },

            # 北京市 / 北京
            {
                "province": "北京", "city": "北京", "university": "清华大学",
                "title": "学生思想政治辅导员岗", "establishment_type": "事业编制", "salary": "15-22万/年",
                "requirements": ["中共党员", "硕士/博士", "学习成绩优秀，综合素质突出"],
                "apply_url": "http://jobs.tsinghua.edu.cn", "status": "🟢 招聘中"
            },
            {
                "province": "北京", "city": "北京", "university": "北京大学",
                "title": "专职辅导员招聘", "establishment_type": "事业编制", "salary": "15-22万/年",
                "requirements": ["中共党员", "硕士及以上", "热爱学生工作，吃苦耐劳"],
                "apply_url": "https://hr.pku.edu.cn", "status": "🟢 已开启报名"
            },

            # 广东省 / 广州市 & 深圳市
            {
                "province": "广东", "city": "广州", "university": "中山大学",
                "title": "专职辅导员岗位招聘公告", "establishment_type": "事业编制", "salary": "14-20万/年",
                "requirements": ["中共党员", "硕士及以上", "熟练掌握学生思想政治教育方法"],
                "apply_url": "http://uems.sysu.edu.cn", "status": "🟢 已开启报名"
            },
            {
                "province": "广东", "city": "深圳", "university": "深圳大学",
                "title": "专职辅导员 (员额制/事业编制)", "establishment_type": "员额制", "salary": "18-25万/年",
                "requirements": ["中共党员", "硕士及以上", "提供特区高薪与安家补贴"],
                "apply_url": "https://hr.szu.edu.cn", "status": "🟢 招聘中"
            },

            # 四川省 / 成都市
            {
                "province": "四川", "city": "成都", "university": "四川大学",
                "title": "专职辅导员招聘简章", "establishment_type": "事业编制", "salary": "10-15万/年",
                "requirements": ["中共党员", "硕士及以上", "政治素质好，品行端正"],
                "apply_url": "http://rs.scu.edu.cn", "status": "🟢 招聘中"
            },
            {
                "province": "四川", "city": "成都", "university": "电子科技大学",
                "title": "专职辅导员岗招聘", "establishment_type": "事业编制", "salary": "11-16万/年",
                "requirements": ["中共党员", "硕士/博士", "计算机、通信、思政类优先"],
                "apply_url": "http://www.hr.uestc.edu.cn", "status": "🟢 招聘中"
            },

            # 湖北省 / 武汉市
            {
                "province": "湖北", "city": "武汉", "university": "武汉大学",
                "title": "专职辅导员公开招聘公告", "establishment_type": "事业编制", "salary": "11-16万/年",
                "requirements": ["中共党员", "硕士及以上", "抗压能力强"],
                "apply_url": "http://rsb.whu.edu.cn", "status": "🟢 招聘中"
            },
            {
                "province": "湖北", "city": "武汉", "university": "华中科技大学",
                "title": "辅导员岗位选拔公告", "establishment_type": "事业编制", "salary": "12-17万/年",
                "requirements": ["中共党员", "硕士及以上", "学生干部背景优先"],
                "apply_url": "http://hr.hust.edu.cn", "status": "🟢 招聘中"
            },

            # 上海市 / 上海
            {
                "province": "上海", "city": "上海", "university": "复旦大学",
                "title": "专职辅导员选拔招聘", "establishment_type": "事业编制", "salary": "14-20万/年",
                "requirements": ["中共党员", "硕士/博士", "优秀的组织协调与文字表达能力"],
                "apply_url": "http://www.hr.fudan.edu.cn", "status": "🟢 已开启报名"
            },
            {
                "province": "上海", "city": "上海", "university": "上海交通大学",
                "title": "思政教师与专职辅导员", "establishment_type": "事业编制", "salary": "15-22万/年",
                "requirements": ["中共党员", "硕士及以上", "综合素质扎实"],
                "apply_url": "https://join.sjtu.edu.cn", "status": "🟢 已开启报名"
            }
        ]

        results: List[CounselorJobItem] = []

        for item in counselor_data_pool:
            match_prov = (province == "all" or province in item["province"] or item["province"] in province)
            match_city = (city == "all" or city in item["city"] or item["city"] in city)

            if match_prov and match_city:
                fp_str = f"{item['university']}_{item['title']}_{item['province']}_{item['city']}"
                job_id = f"counselor_{hashlib.md5(fp_str.encode('utf-8')).hexdigest()[:12]}"

                results.append(CounselorJobItem(
                    id=job_id,
                    university=item["university"],
                    province=item["province"],
                    city=item["city"],
                    title=item["title"],
                    establishment_type=item["establishment_type"],
                    salary=item["salary"],
                    requirements=item["requirements"],
                    apply_url=item["apply_url"],
                    status=item["status"],
                    fetched_at=batch_timestamp
                ))

        return results
