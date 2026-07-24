import os
import sqlite3
import json
from typing import List, Dict
from datetime import datetime
from src.models import JobItem


class JobDatabase:
    """基于 SQLite 的本地岗位与投递状态持久化数据库"""

    def __init__(self, db_path: str = "data/jobhunter.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化 SQLite 表结构"""
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                company_type TEXT,
                company_size TEXT,
                salary TEXT,
                location TEXT,
                batch TEXT,
                match_score INTEGER,
                recommend_reason TEXT,
                requirements TEXT,
                apply_url TEXT,
                tags TEXT,
                status TEXT DEFAULT 'unapplied',
                created_at TEXT
            )
            """)
            conn.commit()

    def save_jobs(self, jobs: List[JobItem]):
        """保存或更新岗位数据到 SQLite (按 ID / 指纹去重与更新)"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            for job in jobs:
                reqs_json = json.dumps(job.requirements, ensure_ascii=False)
                tags_json = json.dumps(job.tags, ensure_ascii=False)

                conn.execute("""
                INSERT INTO jobs (
                    id, title, company, company_type, company_size, 
                    salary, location, batch, match_score, recommend_reason, 
                    requirements, apply_url, tags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    company=excluded.company,
                    salary=excluded.salary,
                    match_score=excluded.match_score,
                    recommend_reason=excluded.recommend_reason,
                    apply_url=excluded.apply_url,
                    tags=excluded.tags
                """, (
                    job.id, job.title, job.company, job.company_type, job.company_size,
                    job.salary, job.location, job.batch, job.match_score, job.recommend_reason,
                    reqs_json, job.apply_url, tags_json, now_str
                ))
            conn.commit()

    def get_all_jobs(self) -> List[JobItem]:
        """获取本地数据库中存留的所有历史岗位记录"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC, match_score DESC").fetchall()
            jobs = []
            for r in rows:
                reqs = json.loads(r["requirements"]) if r["requirements"] else []
                tags = json.loads(r["tags"]) if r["tags"] else []
                jobs.append(JobItem(
                    id=r["id"],
                    title=r["title"],
                    company=r["company"],
                    company_type=r["company_type"] or "",
                    company_size=r["company_size"] or "",
                    salary=r["salary"] or "面议",
                    location=r["location"] or "",
                    batch=r["batch"] or "",
                    match_score=r["match_score"] or 0,
                    recommend_reason=r["recommend_reason"] or "",
                    requirements=reqs,
                    apply_url=r["apply_url"] or "",
                    tags=tags
                ))
            return jobs

    def export_to_json(self, output_json_path: str = "output/data.json", profile_dict: Dict = None, enterprises_list: List[Dict] = None):
        """将本地 SQLite 中的数据导出为独立的 output/data.json 文件供本地 index 页面无缝载入"""
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        jobs = [j.model_dump() for j in self.get_all_jobs()]
        
        data_payload = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": profile_dict or {},
            "jobs_count": len(jobs),
            "jobs": jobs,
            "enterprises": enterprises_list or []
        }

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(data_payload, f, ensure_ascii=False, indent=2)

        print(f"📦 已将本地全量数据导出至: {output_json_path}")
