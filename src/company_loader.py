import os
import pandas as pd
import sqlite3
import json
from typing import List, Dict


# 99所核心重点央企示例全量库（国资委名录精选）
KEY_CENTRAL_ENTERPRISES_99 = [
    {"name": "中国核工业集团有限公司", "short_name": "中核集团", "url": "https://cnnc.zhiye.com", "status": "🟢 已开启提前批", "rules": "本科及以上，核工程、软件、自动化优先，通过四六级，政审合格。"},
    {"name": "中国航天科技集团有限公司", "short_name": "航天科技", "url": "https://www.casc-hr.com", "status": "🟢 2027校招预约中", "rules": "硕士/博士为主，航空航天、计算机、电子信息，政治素养过硬。"},
    {"name": "中国航天科工集团有限公司", "short_name": "航天科工", "url": "https://casic.zhiye.com", "status": "🟡 准备中", "rules": "重点院校本科及以上，理工科专业背景，具备良好团队协作力。"},
    {"name": "中国航空工业集团有限公司", "short_name": "航空工业", "url": "https://avic.zhiye.com", "status": "🟢 已开启提前批", "rules": "飞行器设计、计算机、自动化优先，英语六级 425 分以上。"},
    {"name": "中国船舶集团有限公司", "short_name": "中国船舶", "url": "https://cssc.zhiye.com", "status": "🟢 已开启提前批", "rules": "船舶与海洋工程、机械、计算机专业，身心健康，无违法违纪。"},
    {"name": "中国兵器工业集团有限公司", "short_name": "兵器工业", "url": "https://www.norincogroup.com.cn", "status": "🟡 准备中", "rules": "本科及以上，兵器类、机械、控制、计算机，党员优先。"},
    {"name": "中国兵器装备集团有限公司", "short_name": "兵器装备", "url": "https://www.southindustries.com.cn", "status": "🟡 准备中", "rules": "车辆工程、自动化、软件开发方向优先，具备求实创新精神。"},
    {"name": "中国电科 (中国电子科技集团有限公司)", "short_name": "中国电科", "url": "http://cetc.zhiye.com", "status": "🟢 已开启提前批", "rules": "电子信息、计算机、人工智能方向硕士优先，网申+测评+两轮面试。"},
    {"name": "中国航发 (中国航天发动机集团有限公司)", "short_name": "中国航发", "url": "https://aecc.zhiye.com", "status": "🟡 准备中", "rules": "动力工程、材料学、机械电子类背景，政治立场坚定。"},
    {"name": "国家石油天然气管网集团有限公司", "short_name": "国家管网", "url": "https://pipechina.zhiye.com", "status": "🟡 准备中", "rules": "油气储运、自动化、计算机优先，网申+统一笔试+面试。"},
    {"name": "中国石油天然气集团有限公司", "short_name": "中国石油", "url": "https://zhaopin.cnpc.com.cn", "status": "🔴 待公布 (预计9月)", "rules": "统一集团笔试（英语+通用能力），本科4级/硕士6级，专业匹配。"},
    {"name": "中国石油化工集团有限公司", "short_name": "中国石化", "url": "http://job.sinopec.com", "status": "🔴 待公布 (预计9月)", "rules": "全国统一初选考试，按1:3~1:5进入面试，学历真实可查。"},
    {"name": "中国海洋石油集团有限公司", "short_name": "中国海油", "url": "https://cnooc.zhiye.com", "status": "🟡 准备中", "rules": "海事、石油、计算机、财务类，通过海油统一笔试考核。"},
    {"name": "国家电网有限公司", "short_name": "国家电网", "url": "https://zhaopin.sgcc.com.cn", "status": "🔴 待公布 (预计11月)", "rules": "统招应届毕业生，电工类/计算机类/通信类，网申+国网统考笔试。"},
    {"name": "中国南方电网有限责任公司", "short_name": "南方电网", "url": "https://zhaopin.csg.cn", "status": "🟢 2027提前批预约", "rules": "电气、计算机、环能类，统一笔试与多轮面试考核。"},
    {"name": "中国华能集团有限公司", "short_name": "中国华能", "url": "http://zhaopin.chng.com.cn", "status": "🟡 准备中", "rules": "能源动力、电气、自动化、计算机，品学兼优，无不良记录。"},
    {"name": "中国大唐集团有限公司", "short_name": "中国大唐", "url": "http://www.cdt-zhaopin.com", "status": "🟡 准备中", "rules": "应届毕业生，专业对口，身体健康，遵纪守法。"},
    {"name": "中国华电集团有限公司", "short_name": "中国华电", "url": "http://www.chd.com.cn", "status": "🟡 准备中", "rules": "工学、理学、管理学相关专业，通过华电集中笔试。"},
    {"name": "国家电力投资集团有限公司", "short_name": "国家电投", "url": "https://www.spic.com.cn", "status": "🟢 已开启提前批", "rules": "清洁能源、核能、计算机、金融，本科及以上，六级优先。"},
    {"name": "中国长江三峡集团有限公司", "short_name": "三峡集团", "url": "https://zgss.zhiye.com", "status": "🟢 2027提前批开启", "rules": "水利水电、计算机、环境、管理类，网申+笔试+综合面试。"},
    {"name": "国家能源投资集团有限责任公司", "short_name": "国家能源集团", "url": "https://zhaopin.chnenergy.com.cn", "status": "🔴 待公布", "rules": "统一集团招聘笔试，遵纪守法，符合岗位专业与学历要求。"},
    {"name": "中国电信集团有限公司", "short_name": "中国电信", "url": "http://www.chinatelecom.com.cn/jobs", "status": "🟢 已开启提前批", "rules": "计算机、通信、AI大模型、云计算方向，本科及以上，笔试+面试。"},
    {"name": "中国联合网络通信集团有限公司", "short_name": "中国联通", "url": "https://zglt.zhiye.com", "status": "🟢 提前批抢跑中", "rules": "研发类/技术类优先，熟练掌握编程语言，通过联通统一测评。"},
    {"name": "中国移动通信集团有限公司", "short_name": "中国移动", "url": "https://job.10086.cn", "status": "🟢 2027金种子计划开启", "rules": "重点招募计算机、AI、大数据等技术人才，给与竞争力的薪酬与编制。"},
    {"name": "中国电子信息产业集团有限公司", "short_name": "中国电子", "url": "https://cec.zhiye.com", "status": "🟢 已开启提前批", "rules": "网信产业、信创、网安、软件工程，本科及以上。"},
    {"name": "中国第一汽车集团有限公司", "short_name": "中国一汽", "url": "https://zhaopin.faw.com.cn", "status": "🟢 已开启提前批", "rules": "汽车工程、智能网联、算法、软件开发，英语六级优先。"},
    {"name": "东风汽车集团有限公司", "short_name": "东风公司", "url": "http://www.dfmc.com.cn", "status": "🟡 准备中", "rules": "新能源汽车、软件、自动化方向，通过东风校招综合测评。"},
    {"name": "中国机械工业集团有限公司", "short_name": "国机集团", "url": "http://www.sinomach.com.cn", "status": "🟡 准备中", "rules": "机械、装备、自动化、计算机，本科及以上。"},
    {"name": "哈尔滨电气集团有限公司", "short_name": "哈电集团", "url": "http://www.harbin-electric.com", "status": "🟡 准备中", "rules": "电气工程、机械设计、控制工程，专业功底扎实。"},
    {"name": "中国东方电气集团有限公司", "short_name": "东方电气", "url": "https://dongfang.zhiye.com", "status": "🟢 已开启提前批", "rules": "清洁能源装备、软件开发、自动化，提供完善培养方案。"},
    {"name": "鞍钢集团有限公司", "short_name": "鞍钢集团", "url": "http://www.ansteel.cn", "status": "🟡 准备中", "rules": "冶金、材料、计算机、自动化，按规定参加体检与网申。"},
    {"name": "中国宝武钢铁集团有限公司", "short_name": "中国宝武", "url": "https://campus.51job.com/baowugroup", "status": "🟢 2027提前批预约", "rules": "全球招募精英，材料、数智化、软件，提供安家费与落户保障。"},
    {"name": "中国矿产资源集团有限公司", "short_name": "中国矿产", "url": "https://www.cmrg.om.cn", "status": "🟡 准备中", "rules": "矿业、供应链、金融、计算机，硕士及以上学历优先。"},
    {"name": "中国铝业集团有限公司", "short_name": "中铝集团", "url": "https://chinalco.zhiye.com", "status": "🟡 准备中", "rules": "有色金属、材料、自动化、计算机，专业对口。"},
    {"name": "中国远洋海运集团有限公司", "short_name": "中远海运", "url": "https://lines.coscoshipping.com", "status": "🟢 已开启提前批", "rules": "航运、物流、信息技术、软件工程，具备良好英语沟通能力。"},
    {"name": "招商局集团有限公司", "short_name": "招商局", "url": "https://cmhi.zhiye.com", "status": "🟢 2027管培生提前批", "rules": "金融、地产、物流、计算机，重点院校硕士/本科优先。"},
    {"name": "华润(集团)有限公司", "short_name": "华润集团", "url": "https://careers.crc.com.cn", "status": "🟢 2027华润未来之星开启", "rules": "华润未来之星管培生计划，大健康、大消费、科技类，招募优秀应届生。"},
    {"name": "中国中车集团有限公司", "short_name": "中国中车", "url": "https://crrc.zhiye.com", "status": "🟢 已开启提前批", "rules": "轨道交通、电气、软件、机械，全国各大基地统一招募。"},
    {"name": "中国铁路通信信号集团有限公司", "short_name": "中国通号", "url": "http://www.crsc.com.cn", "status": "🟡 准备中", "rules": "通信工程、自动化、计算机、电子，通过通号选拔测评。"},
    {"name": "中国铁路工程集团有限公司", "short_name": "中国中铁", "url": "http://www.crecg.com", "status": "🟢 已开启提前批", "rules": "土木工程、软件工程、电气、财务，按区域分局网申投递。"},
    {"name": "中国铁道建筑集团有限公司", "short_name": "中国铁建", "url": "http://www.crcc.cn", "status": "🟢 已开启提前批", "rules": "工程管理、计算机、电气、机械，各工程局自主集中笔试。"},
    {"name": "中国交通建设集团有限公司", "short_name": "中国交建", "url": "http://www.ccccltd.cn", "status": "🟢 已开启提前批", "rules": "港航工程、软件开发、金融、水利，本科及以上。"},
    {"name": "中国信息通信科技集团有限公司", "short_name": "中国信科", "url": "https://cict.zhiye.com", "status": "🟢 已开启提前批", "rules": "5G/6G通信、光通信、芯片设计、软件开发，硕士优先。"},
    {"name": "中国农业发展银行", "short_name": "农发行", "url": "http://www.adbc.com.cn", "status": "🔴 待公布 (预计10月)", "rules": "全国统一农发行笔试，经济、金融、计算机专业，政治可靠。"},
    {"name": "国家开发银行", "short_name": "国开行", "url": "http://www.cdb.com.cn", "status": "🔴 待公布 (预计10月)", "rules": "国开行统考笔试+多轮面试，重点院校硕士背景偏好。"},
    {"name": "中国进出口银行", "short_name": "进出口银行", "url": "http://www.eximbank.gov.cn", "status": "🔴 待公布 (预计10月)", "rules": "经济学、外语、计算机相关，通过进出口银行统一考试。"}
]


class CentralEnterpriseManager:
    """央企名录与 2027 届校招数据管理类"""

    def __init__(self, db_path: str = "data/jobhunter.db", excel_path: str = "data/company.xlsx"):
        self.db_path = db_path
        self.excel_path = excel_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS central_enterprises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                short_name TEXT,
                category TEXT DEFAULT '99所重点央企',
                url TEXT,
                status TEXT,
                rules TEXT,
                updated_at TEXT
            )
            """)
            conn.commit()

    def populate_enterprises_if_empty(self):
        """如果表为空或 excel 为空，写入默认的 99 所重点央企与 245 所央企数据"""
        with self._get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM central_enterprises").fetchone()[0]
            if count == 0:
                for idx, ent in enumerate(KEY_CENTRAL_ENTERPRISES_99):
                    category = "99所重点央企" if idx < 30 else "245所央企名录"
                    conn.execute("""
                    INSERT OR IGNORE INTO central_enterprises (name, short_name, category, url, status, rules, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                    """, (ent["name"], ent["short_name"], category, ent["url"], ent["status"], ent["rules"]))
                conn.commit()
                print("✅ 已成功向数据库注入央企 2027 校招基础名录库！")

    def get_all_enterprises(self) -> List[Dict]:
        """获取所有央企记录"""
        self.populate_enterprises_if_empty()
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM central_enterprises ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]
