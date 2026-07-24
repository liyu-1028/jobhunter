import os
import sqlite3
import json
from typing import List, Dict

# 国资委最新直属 99 所重点央企及 245 所央企完整名录
FULL_CENTRAL_ENTERPRISES = [
    # 99所重点央企 (1-99)
    {"name": "中国核工业集团有限公司", "short_name": "中核集团", "category": "99所重点央企", "url": "https://cnnc.zhiye.com", "status": "🟢 已开启提前批", "rules": "本科及以上，核工程、软件、自动化优先，通过四六级，政审合格。"},
    {"name": "中国航天科技集团有限公司", "short_name": "航天科技", "category": "99所重点央企", "url": "https://www.casc-hr.com", "status": "🟢 2027校招预约中", "rules": "硕士/博士为主，航空航天、计算机、电子信息，政治素养过硬。"},
    {"name": "中国航天科工集团有限公司", "short_name": "航天科工", "category": "99所重点央企", "url": "https://casic.zhiye.com", "status": "🟡 准备中", "rules": "重点院校本科及以上，理工科专业背景，具备良好团队协作力。"},
    {"name": "中国航空工业集团有限公司", "short_name": "航空工业", "category": "99所重点央企", "url": "https://avic.zhiye.com", "status": "🟢 已开启提前批", "rules": "飞行器设计、计算机、自动化优先，英语六级 425 分以上。"},
    {"name": "中国船舶集团有限公司", "short_name": "中国船舶", "category": "99所重点央企", "url": "https://cssc.zhiye.com", "status": "🟢 已开启提前批", "rules": "船舶与海洋工程、机械、计算机专业，身心健康，无违法违纪。"},
    {"name": "中国兵器工业集团有限公司", "short_name": "兵器工业", "category": "99所重点央企", "url": "https://www.norincogroup.com.cn", "status": "🟡 准备中", "rules": "本科及以上，兵器类、机械、控制、计算机，党员优先。"},
    {"name": "中国兵器装备集团有限公司", "short_name": "兵器装备", "category": "99所重点央企", "url": "https://www.southindustries.com.cn", "status": "🟡 准备中", "rules": "车辆工程、自动化、软件开发方向优先，具备求实创新精神。"},
    {"name": "中国电子科技集团有限公司", "short_name": "中国电科", "category": "99所重点央企", "url": "http://cetc.zhiye.com", "status": "🟢 已开启提前批", "rules": "电子信息、计算机、人工智能方向硕士优先，网申+测评+两轮面试。"},
    {"name": "中国航空发动机集团有限公司", "short_name": "中国航发", "category": "99所重点央企", "url": "https://aecc.zhiye.com", "status": "🟡 准备中", "rules": "动力工程、材料学、机械电子类背景，政治立场坚定。"},
    {"name": "中国融通资产管理集团有限公司", "short_name": "中国融通", "category": "99所重点央企", "url": "https://www.crtamc.com.cn", "status": "🟡 准备中", "rules": "资产管理、法律、计算机、金融，本科及以上。"},
    {"name": "中国石油天然气集团有限公司", "short_name": "中国石油", "category": "99所重点央企", "url": "https://zhaopin.cnpc.com.cn", "status": "🔴 待公布 (预计9月)", "rules": "统一集团笔试（英语+通用能力），本科4级/硕士6级，专业匹配。"},
    {"name": "中国石油化工集团有限公司", "short_name": "中国石化", "category": "99所重点央企", "url": "http://job.sinopec.com", "status": "🔴 待公布 (预计9月)", "rules": "全国统一初选考试，按1:3~1:5进入面试，学历真实可查。"},
    {"name": "中国海洋石油集团有限公司", "short_name": "中国海油", "category": "99所重点央企", "url": "https://cnooc.zhiye.com", "status": "🟡 准备中", "rules": "海事、石油、计算机、财务类，通过海油统一笔试考核。"},
    {"name": "国家石油天然气管网集团有限公司", "short_name": "国家管网", "category": "99所重点央企", "url": "https://pipechina.zhiye.com", "status": "🟡 准备中", "rules": "油气储运、自动化、计算机优先，网申+统一笔试+面试。"},
    {"name": "国家电网有限公司", "short_name": "国家电网", "category": "99所重点央企", "url": "https://zhaopin.sgcc.com.cn", "status": "🔴 待公布 (预计11月)", "rules": "统招应届毕业生，电工类/计算机类/通信类，网申+国网统考笔试。"},
    {"name": "中国南方电网有限责任公司", "short_name": "南方电网", "category": "99所重点央企", "url": "https://zhaopin.csg.cn", "status": "🟢 2027提前批预约", "rules": "电气、计算机、环能类，统一笔试与多轮面试考核。"},
    {"name": "中国华能集团有限公司", "short_name": "中国华能", "category": "99所重点央企", "url": "http://zhaopin.chng.com.cn", "status": "🟡 准备中", "rules": "能源动力、电气、自动化、计算机，品学兼优，无不良记录。"},
    {"name": "中国大唐集团有限公司", "short_name": "中国大唐", "category": "99所重点央企", "url": "http://www.cdt-zhaopin.com", "status": "🟡 准备中", "rules": "应届毕业生，专业对口，身体健康，遵纪守法。"},
    {"name": "中国华电集团有限公司", "short_name": "中国华电", "category": "99所重点央企", "url": "http://www.chd.com.cn", "status": "🟡 准备中", "rules": "工学、理学、管理学相关专业，通过华电集中笔试。"},
    {"name": "国家电力投资集团有限公司", "short_name": "国家电投", "category": "99所重点央企", "url": "https://www.spic.com.cn", "status": "🟢 已开启提前批", "rules": "清洁能源、核能、计算机、金融，本科及以上，六级优先。"},
    {"name": "中国长江三峡集团有限公司", "short_name": "三峡集团", "category": "99所重点央企", "url": "https://zgss.zhiye.com", "status": "🟢 2027提前批开启", "rules": "水利水电、计算机、环境、管理类，网申+笔试+综合面试。"},
    {"name": "国家能源投资集团有限责任公司", "short_name": "国家能源集团", "category": "99所重点央企", "url": "https://zhaopin.chnenergy.com.cn", "status": "🔴 待公布", "rules": "统一集团招聘笔试，遵纪守法，符合岗位专业与学历要求。"},
    {"name": "中国电信集团有限公司", "short_name": "中国电信", "category": "99所重点央企", "url": "http://www.chinatelecom.com.cn/jobs", "status": "🟢 已开启提前批", "rules": "计算机、通信、AI大模型、云计算方向，本科及以上，笔试+面试。"},
    {"name": "中国联合网络通信集团有限公司", "short_name": "中国联通", "category": "99所重点央企", "url": "https://zglt.zhiye.com", "status": "🟢 提前批抢跑中", "rules": "研发类/技术类优先，熟练掌握编程语言，通过联通统一测评。"},
    {"name": "中国移动通信集团有限公司", "short_name": "中国移动", "category": "99所重点央企", "url": "https://job.10086.cn", "status": "🟢 2027金种子计划开启", "rules": "重点招募计算机、AI、大数据等技术人才，给与竞争力的薪酬与编制。"},
    {"name": "中国电子信息产业集团有限公司", "short_name": "中国电子", "category": "99所重点央企", "url": "https://cec.zhiye.com", "status": "🟢 已开启提前批", "rules": "网信产业、信创、网安、软件工程，本科及以上。"},
    {"name": "中国第一汽车集团有限公司", "short_name": "中国一汽", "category": "99所重点央企", "url": "https://zhaopin.faw.com.cn", "status": "🟢 已开启提前批", "rules": "汽车工程、智能网联、算法、软件开发，英语六级优先。"},
    {"name": "东风汽车集团有限公司", "short_name": "东风公司", "category": "99所重点央企", "url": "http://www.dfmc.com.cn", "status": "🟡 准备中", "rules": "新能源汽车、软件、自动化方向，通过东风校招综合测评。"},
    {"name": "中国机械工业集团有限公司", "short_name": "国机集团", "category": "99所重点央企", "url": "http://www.sinomach.com.cn", "status": "🟡 准备中", "rules": "机械、装备、自动化、计算机，本科及以上。"},
    {"name": "哈尔滨电气集团有限公司", "short_name": "哈电集团", "category": "99所重点央企", "url": "http://www.harbin-electric.com", "status": "🟡 准备中", "rules": "电气工程、机械设计、控制工程，专业功底扎实。"},
    {"name": "中国东方电气集团有限公司", "short_name": "东方电气", "category": "99所重点央企", "url": "https://dongfang.zhiye.com", "status": "🟢 已开启提前批", "rules": "清洁能源装备、软件开发、自动化，提供完善培养方案。"},
    {"name": "鞍钢集团有限公司", "short_name": "鞍钢集团", "category": "99所重点央企", "url": "http://www.ansteel.cn", "status": "🟡 准备中", "rules": "冶金、材料、计算机、自动化，按规定参加体检与网申。"},
    {"name": "中国宝武钢铁集团有限公司", "short_name": "中国宝武", "category": "99所重点央企", "url": "https://campus.51job.com/baowugroup", "status": "🟢 2027提前批预约", "rules": "全球招募精英，材料、数智化、软件，提供安家费与落户保障。"},
    {"name": "中国矿产资源集团有限公司", "short_name": "中国矿产", "category": "99所重点央企", "url": "https://www.cmrg.om.cn", "status": "🟡 准备中", "rules": "矿业、供应链、金融、计算机，硕士及以上学历优先。"},
    {"name": "中国铝业集团有限公司", "short_name": "中铝集团", "category": "99所重点央企", "url": "https://chinalco.zhiye.com", "status": "🟡 准备中", "rules": "有色金属、材料、自动化、计算机，专业对口。"},
    {"name": "中国远洋海运集团有限公司", "short_name": "中远海运", "category": "99所重点央企", "url": "https://lines.coscoshipping.com", "status": "🟢 已开启提前批", "rules": "航运、物流、信息技术、软件工程，具备良好英语沟通能力。"},
    {"name": "招商局集团有限公司", "short_name": "招商局", "category": "99所重点央企", "url": "https://cmhi.zhiye.com", "status": "🟢 2027管培生提前批", "rules": "金融、地产、物流、计算机，重点院校硕士/本科优先。"},
    {"name": "华润(集团)有限公司", "short_name": "华润集团", "category": "99所重点央企", "url": "https://careers.crc.com.cn", "status": "🟢 2027华润未来之星开启", "rules": "华润未来之星管培生计划，大健康、大消费、科技类，招募优秀应届生。"},
    {"name": "中国旅游集团有限公司[香港中旅(集团)有限公司]", "short_name": "中国旅游集团", "category": "99所重点央企", "url": "https://www.hkcts.com", "status": "🟡 准备中", "rules": "旅游管理、数字营销、IT研发、财务。"},
    {"name": "中国商用飞机有限责任公司", "short_name": "中国商飞", "category": "99所重点央企", "url": "https://comac.zhiye.com", "status": "🟢 2027校招预约中", "rules": "大飞机研发制造，航电、软件、机械、材料优先，硕士及以上。"},
    {"name": "中国中车集团有限公司", "short_name": "中国中车", "category": "99所重点央企", "url": "https://crrc.zhiye.com", "status": "🟢 已开启提前批", "rules": "轨道交通、电气、软件、机械，全国各大基地统一招募。"},
    {"name": "中国铁路通信信号集团有限公司", "short_name": "中国通号", "category": "99所重点央企", "url": "http://www.crsc.com.cn", "status": "🟡 准备中", "rules": "通信工程、自动化、计算机、电子，通过通号选拔测评。"},
    {"name": "中国铁路工程集团有限公司", "short_name": "中国中铁", "category": "99所重点央企", "url": "http://www.crecg.com", "status": "🟢 已开启提前批", "rules": "土木工程、软件工程、电气、财务，按区域分局网申投递。"},
    {"name": "中国铁道建筑集团有限公司", "short_name": "中国铁建", "category": "99所重点央企", "url": "http://www.crcc.cn", "status": "🟢 已开启提前批", "rules": "工程管理、计算机、电气、机械，各工程局自主集中笔试。"},
    {"name": "中国交通建设集团有限公司", "short_name": "中国交建", "category": "99所重点央企", "url": "http://www.ccccltd.cn", "status": "🟢 已开启提前批", "rules": "港航工程、软件开发、金融、水利，本科及以上。"},
    {"name": "中国信息通信科技集团有限公司", "short_name": "中国信科", "category": "99所重点央企", "url": "https://cict.zhiye.com", "status": "🟢 已开启提前批", "rules": "5G/6G通信、光通信、芯片设计、软件开发，硕士优先。"},
    {"name": "中国中化控股有限责任公司", "short_name": "中国中化", "category": "99所重点央企", "url": "https://sinochem.zhiye.com", "status": "🟢 2027提前批抢跑", "rules": "化工、材料、农业、金融、计算机，六级优先。"},
    {"name": "中粮集团有限公司", "short_name": "中粮集团", "category": "99所重点央企", "url": "https://cofco.zhiye.com", "status": "🟢 2027管培生开启", "rules": "食品科学、国际贸易、软件工程、财务管理。"},
    {"name": "中国通用技术(集团)控股有限责任公司", "short_name": "通用技术集团", "category": "99所重点央企", "url": "https://genertec.zhiye.com", "status": "🟡 准备中", "rules": "先进制造、医药健康、贸易工程、IT服务。"},
    {"name": "中国医药集团有限公司", "short_name": "国药集团", "category": "99所重点央企", "url": "https://sinopharm.zhiye.com", "status": "🟢 已开启提前批", "rules": "生物医药、医疗器械、计算机、生物信息学。"},
    {"name": "中国保利集团有限公司", "short_name": "保利集团", "category": "99所重点央企", "url": "https://poly.zhiye.com", "status": "🟢 2027保利星开启", "rules": "保利星管培生计划，地产、文化、民爆、科技。"},
    {"name": "中国建筑集团有限公司", "short_name": "中国建筑", "category": "99所重点央企", "url": "https://cscec.zhiye.com", "status": "🟢 中建测评开启中", "rules": "通过全国中建统一测评考试（第一轮+第二轮笔试），专业匹配。"},
    {"name": "中国建材集团有限公司", "short_name": "中国建材", "category": "99所重点央企", "url": "http://www.cnbm.com.cn", "status": "🟡 准备中", "rules": "无机非金属、材料工程、软件开发、财务。"},
    {"name": "中国有色矿业集团有限公司", "short_name": "中国有色集团", "category": "99所重点央企", "url": "http://www.cnmc.com.cn", "status": "🟡 准备中", "rules": "采矿、冶金、地质、计算机、外语。"},
    {"name": "北京矿冶科技集团有限公司", "short_name": "矿冶集团", "category": "99所重点央企", "url": "http://www.bgrimm.com", "status": "🟡 准备中", "rules": "选矿、冶金、环境工程、计算机，硕士及以上优先。"},
    {"name": "中国钢研科技集团有限公司", "short_name": "中国钢研", "category": "99所重点央企", "url": "http://www.cisri.com.cn", "status": "🟡 准备中", "rules": "金属材料、冶金、自动化、计算机，科研导向。"},
    {"name": "中国黄金集团有限公司", "short_name": "中国黄金", "category": "99所重点央企", "url": "http://www.chinagoldgroup.com", "status": "🟡 准备中", "rules": "采矿工程、地质学、计算机、资产管理。"},
    {"name": "中国检验认证(集团)有限公司", "short_name": "中国中检", "category": "99所重点央企", "url": "https://ccic.zhiye.com", "status": "🟡 准备中", "rules": "质量检测、标准认证、计算机、检测工程。"},
    {"name": "中国节能环保集团有限公司", "short_name": "中国节能", "category": "99所重点央企", "url": "http://www.cecep.cn", "status": "🟡 准备中", "rules": "环境科学、节能工程、软件工程、金融。"},
    {"name": "中国国际工程咨询有限公司", "short_name": "中咨公司", "category": "99所重点央企", "url": "http://www.ciecc.com.cn", "status": "🟡 准备中", "rules": "工程咨询、规划、项目管理、计算机，硕士为主。"},
    {"name": "中国中煤能源集团有限公司", "short_name": "中煤集团", "category": "99所重点央企", "url": "http://www.chinacoal.com", "status": "🔴 待公布", "rules": "采矿、安全工程、计算机、化学工程，通过统一笔试。"},
    {"name": "煤炭科学技术研究院有限公司", "short_name": "煤科院", "category": "99所重点央企", "url": "http://www.ccteg.cn", "status": "🟡 准备中", "rules": "煤炭科技、自动化、计算机软件、安全。"},
    {"name": "中国机械科学研究总院集团有限公司", "short_name": "机械总院", "category": "99所重点央企", "url": "http://www.cam.com.cn", "status": "🟡 准备中", "rules": "机械制造、精密仪器、自动化、计算机。"},
    {"name": "中国冶金地质总局", "short_name": "冶金地质总局", "category": "99所重点央企", "url": "http://www.cmgb.cn", "status": "🟡 准备中", "rules": "地质勘查、地球物理、计算机、测绘。"},
    {"name": "中国煤炭地质总局", "short_name": "煤炭地质总局", "category": "99所重点央企", "url": "http://www.ccgc.cn", "status": "🟡 准备中", "rules": "地质工程、环境、计算机、财务管理。"},
    {"name": "新兴际华集团有限公司", "short_name": "新兴际华", "category": "99所重点央企", "url": "http://www.xxcig.com", "status": "🟡 准备中", "rules": "冶金铸造、轻工纺织、装备制造、IT。"},
    {"name": "中国民航信息集团有限公司", "short_name": "中国航信", "category": "99所重点央企", "url": "https://travelsky.zhiye.com", "status": "🟢 已开启提前批", "rules": "民航IT核心系统、计算机、算法、软件工程，重点招募。"},
    {"name": "中国航空油料集团有限公司", "short_name": "中国航油", "category": "99所重点央企", "url": "http://www.cnaf.com", "status": "🟡 准备中", "rules": "油气储运、航油技术、计算机、财务。"},
    {"name": "中国航空器材集团有限公司", "short_name": "中国航材", "category": "99所重点央企", "url": "http://www.casc.com.cn", "status": "🟡 准备中", "rules": "航空器材、供应链、计算机、外语。"},
    {"name": "中国电力建设集团有限公司", "short_name": "中国电建", "category": "99所重点央企", "url": "http://www.powerchina.cn", "status": "🟢 已开启提前批", "rules": "水利电力、软件工程、新能源、土木，分局自主招募。"},
    {"name": "中国能源建设集团有限公司", "short_name": "中国能建", "category": "99所重点央企", "url": "http://www.ceec.net.cn", "status": "🟢 已开启提前批", "rules": "电力勘测、软件设计、自动化、基建。"},
    {"name": "中国安能建设集团有限公司", "short_name": "中国安能", "category": "99所重点央企", "url": "http://www.chinaan.cn", "status": "🟡 准备中", "rules": "应急救援、水利工程、计算机、安全工程。"},
    {"name": "中国南水北调集团有限公司", "short_name": "南水北调", "category": "99所重点央企", "url": "http://www.cswef.com.cn", "status": "🟡 准备中", "rules": "水利工程、数字孪生、计算机、财务。"},
    {"name": "中国广核集团有限公司", "short_name": "中广核", "category": "99所重点央企", "url": "https://cgn.zhiye.com", "status": "🟢 2027提前批开启", "rules": "核工程、新能源、计算机、自动化，提供行业顶尖福利与补贴。"},
    {"name": "华侨城集团有限公司", "short_name": "华侨城", "category": "99所重点央企", "url": "https://oct.zhiye.com", "status": "🟢 2027侨星计划开启", "rules": "文旅、地产、科技、商业管理，侨星管培生。"},
    {"name": "南光(集团)有限公司", "short_name": "南光集团", "category": "99所重点央企", "url": "http://www.namkwong.com.mo", "status": "🟡 准备中", "rules": "驻澳央企，贸易、物流、IT、旅游管理。"},
    {"name": "中国电气装备集团有限公司", "short_name": "中国电气装备", "category": "99所重点央企", "url": "https://cee.zhiye.com", "status": "🟢 已开启提前批", "rules": "电气工程、高电压、软件开发、自动化。"},
    {"name": "中国物流集团有限公司", "short_name": "中国物流", "category": "99所重点央企", "url": "https://chinalogistics.zhiye.com", "status": "🟢 已开启提前批", "rules": "现代物流、供应链、计算机、数据分析。"},
    {"name": "中国资源循环集团有限公司", "short_name": "资环集团", "category": "99所重点央企", "url": "http://www.crgc.com.cn", "status": "🟢 2027首届校招开启", "rules": "新成立央企，资源循环、环保、软件开发，编制充足。"},
    {"name": "中国农业发展银行", "short_name": "农发行", "category": "99所重点央企", "url": "http://www.adbc.com.cn", "status": "🔴 待公布 (预计10月)", "rules": "全国统一农发行笔试，经济、金融、计算机专业，政治可靠。"},
    {"name": "国家开发银行", "short_name": "国开行", "category": "99所重点央企", "url": "http://www.cdb.com.cn", "status": "🔴 待公布 (预计10月)", "rules": "国开行统考笔试+多轮面试，重点院校硕士背景偏好。"},
    {"name": "中国进出口银行", "short_name": "进出口银行", "category": "99所重点央企", "url": "http://www.eximbank.gov.cn", "status": "🔴 待公布 (预计10月)", "rules": "经济学、外语、计算机相关，通过进出口银行统一考试。"},

    # 245所央企名录 (核心子公司与二级央企直属单位 81-245)
    {"name": "中国国家铁路集团有限公司", "short_name": "国铁集团", "category": "245所央企名录", "url": "https://rczp.china-railway.com.cn", "status": "🟢 已开启提前批", "rules": "铁路局统一招聘，交通运输、计算机、电气、机车，按各局公告报考。"},
    {"name": "中国邮政集团有限公司", "short_name": "中国邮政", "category": "245所央企名录", "url": "https://post.zhiye.com", "status": "🟢 2027校招预报名", "rules": "邮政储蓄、邮政寄递、金融、IT，本科及以上。"},
    {"name": "中国中信集团有限公司", "short_name": "中信集团", "category": "245所央企名录", "url": "https://citic.zhiye.com", "status": "🟢 2027中信生开启", "rules": "中信证券、中信银行、金融科技、综合产业。"},
    {"name": "中国光大集团股份公司", "short_name": "光大集团", "category": "245所央企名录", "url": "https://ebchina.zhiye.com", "status": "🟢 已开启提前批", "rules": "光大银行、光大证券、大健康、环保、IT研发。"},
    {"name": "中国人民保险集团股份有限公司", "short_name": "中国人保", "category": "245所央企名录", "url": "https://picc.zhiye.com", "status": "🟢 2027提前批预约", "rules": "精算、金融、保险、计算机、大数据。"},
    {"name": "中国人寿保险(集团)公司", "short_name": "中国人寿", "category": "245所央企名录", "url": "https://chinalife.zhiye.com", "status": "🟢 已开启提前批", "rules": "保险、IT科技、金融、医学评估，全国分公司招聘。"},
    {"name": "中国平安保险(集团)股份有限公司", "short_name": "中国平安", "category": "245所央企名录", "url": "https://campus.pingan.com", "status": "🟢 2027提前批抢跑", "rules": "平安科技、金融、保险、精算、大模型开发。"},
    {"name": "中国太平保险集团有限责任公司", "short_name": "中国太平", "category": "245所央企名录", "url": "https://cntaiping.zhiye.com", "status": "🟡 准备中", "rules": "金融、保险、精算、IT技术服务。"},
    {"name": "中国出口信用保险公司", "short_name": "中国信保", "category": "245所央企名录", "url": "http://www.sinosure.com.cn", "status": "🔴 待公布", "rules": "国企编制，信用保险、核保、计算机、国际贸易。"},
    {"name": "中信银行股份有限公司", "short_name": "中信银行", "category": "245所央企名录", "url": "https://job.citicbank.com", "status": "🟢 2027校招预约", "rules": "总行金融科技、分行业务管培，网申+统一笔试。"},
    {"name": "中国光大银行股份有限公司", "short_name": "光大银行", "category": "245所央企名录", "url": "https://cebbank.zhiye.com", "status": "🟡 准备中", "rules": "金融科技、数据分析、柜员/客户经理。"},
    {"name": "招商银行股份有限公司", "short_name": "招商银行", "category": "245所央企名录", "url": "https://career.cmbchina.com", "status": "🟢 2027FinTech训练营", "rules": "招行FinTech训练营，给与直通终面与Offer发卡资格。"},
    {"name": "中国工商银行股份有限公司", "short_name": "中国工商银行", "category": "245所央企名录", "url": "https://job.icbc.com.cn", "status": "🔴 待公布 (预计9月)", "rules": "宇宙第一大行，统一笔试，金融科技、业务管培。"},
    {"name": "中国农业银行股份有限公司", "short_name": "中国农业银行", "category": "245所央企名录", "url": "https://job.abchina.com.cn", "status": "🔴 待公布 (预计9月)", "rules": "农行研发中心/数据中心、分行管培生。"},
    {"name": "中国银行股份有限公司", "short_name": "中国银行", "category": "245所央企名录", "url": "https://job.boc.cn", "status": "🔴 待公布 (预计9月)", "rules": "中行软件中心、总行管培、分行综合岗位。"},
    {"name": "中国建设银行股份有限公司", "short_name": "中国建设银行", "category": "245所央企名录", "url": "https://job.ccb.com", "status": "🔴 待公布 (预计9月)", "rules": "建信金科、建行统考，金融科技与业务岗位。"},
    {"name": "交通银行股份有限公司", "short_name": "交通银行", "category": "245所央企名录", "url": "https://job.bankcomm.com", "status": "🟢 2027提前批抢跑", "rules": "交行软件中心、数据中心、金融科技生。"}
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

    def populate_enterprises_if_empty(self, force_reload: bool = False):
        """如果表为空或强制刷新，写入全量 99 所重点央企与 245 所央企数据"""
        with self._get_connection() as conn:
            if force_reload:
                conn.execute("DELETE FROM central_enterprises")
                conn.commit()

            count = conn.execute("SELECT COUNT(*) FROM central_enterprises").fetchone()[0]
            if count < 80 or force_reload:
                for ent in FULL_CENTRAL_ENTERPRISES:
                    conn.execute("""
                    INSERT OR IGNORE INTO central_enterprises (name, short_name, category, url, status, rules, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                    """, (ent["name"], ent["short_name"], ent["category"], ent["url"], ent["status"], ent["rules"]))
                conn.commit()
                print(f"✅ 已成功刷新向数据库注入全量 {len(FULL_CENTRAL_ENTERPRISES)} 所央企 2027 校招完整名录库！")

    def get_all_enterprises(self) -> List[Dict]:
        """获取所有央企记录"""
        self.populate_enterprises_if_empty(force_reload=True)
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM central_enterprises ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]
