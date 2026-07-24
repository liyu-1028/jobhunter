import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from src.models import JobItem, CounselorJobItem

class JobDatabase:
    """本地 SQLite 岗位、央企与高校辅导员持久化数据库类"""

    def __init__(self, db_path: str = "data/jobhunter.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # 自动迁移检查旧 jobs 表
            try:
                conn.execute("SELECT requirements_json FROM jobs LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute("DROP TABLE IF EXISTS jobs")

            # 岗位表 (带 fetched_at 批次时间戳)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                company_type TEXT,
                company_size TEXT,
                location TEXT,
                salary TEXT,
                batch TEXT,
                match_score INTEGER,
                recommend_reason TEXT,
                requirements_json TEXT,
                tags_json TEXT,
                apply_url TEXT,
                source TEXT,
                fetched_at TEXT,
                created_at TEXT
            )
            """)

            # 高校辅导员岗位表 (带 fetched_at 批次时间戳)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS counselor_jobs (
                id TEXT PRIMARY KEY,
                university TEXT NOT NULL,
                province TEXT NOT NULL,
                city TEXT NOT NULL,
                title TEXT NOT NULL,
                establishment_type TEXT,
                salary TEXT,
                requirements_json TEXT,
                apply_url TEXT,
                status TEXT,
                fetched_at TEXT,
                created_at TEXT
            )
            """)
            conn.commit()

    def save_jobs(self, jobs: List[JobItem], batch_timestamp: str = None) -> int:
        """保存或更新岗位记录，打上批次时间戳"""
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        inserted_count = 0
        with self._get_connection() as conn:
            for job in jobs:
                req_json = json.dumps(job.requirements, ensure_ascii=False)
                tags_json = json.dumps(job.tags, ensure_ascii=False)
                fetched_at = job.fetched_at or batch_timestamp

                conn.execute("""
                INSERT INTO jobs (
                    id, company, title, company_type, company_size, location, salary,
                    batch, match_score, recommend_reason, requirements_json, tags_json,
                    apply_url, source, fetched_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                ON CONFLICT(id) DO UPDATE SET
                    match_score=excluded.match_score,
                    recommend_reason=excluded.recommend_reason,
                    salary=excluded.salary,
                    fetched_at=excluded.fetched_at
                """, (
                    job.id, job.company, job.title, job.company_type, job.company_size,
                    job.location, job.salary, job.batch, job.match_score, job.recommend_reason,
                    req_json, tags_json, job.apply_url, job.source, fetched_at
                ))
                inserted_count += 1
            conn.commit()

        self.export_to_json()
        return inserted_count

    def save_counselor_jobs(self, jobs: List[CounselorJobItem], batch_timestamp: str = None) -> int:
        """保存高校辅导员岗位记录，打上同一批次时间戳"""
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            for job in jobs:
                req_json = json.dumps(job.requirements, ensure_ascii=False)
                fetched_at = job.fetched_at or batch_timestamp

                conn.execute("""
                INSERT INTO counselor_jobs (
                    id, university, province, city, title, establishment_type, salary,
                    requirements_json, apply_url, status, fetched_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    salary=excluded.salary,
                    fetched_at=excluded.fetched_at
                """, (
                    job.id, job.university, job.province, job.city, job.title,
                    job.establishment_type, job.salary, req_json, job.apply_url,
                    job.status, fetched_at
                ))
            conn.commit()

        self.export_to_json()
        return len(jobs)

    def get_all_jobs(self) -> List[Dict]:
        """获取所有岗位记录"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY fetched_at DESC, match_score DESC").fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['requirements'] = json.loads(item['requirements_json']) if item['requirements_json'] else []
                item['tags'] = json.loads(item['tags_json']) if item['tags_json'] else []
                result.append(item)
            return result

    def get_all_counselor_jobs(self) -> List[Dict]:
        """获取所有高校辅导员岗位记录"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM counselor_jobs ORDER BY fetched_at DESC, id ASC").fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['requirements'] = json.loads(item['requirements_json']) if item['requirements_json'] else []
                result.append(item)
            return result

    def export_to_json(self, output_path: str = "output/data.json"):
        """将全量数据导出为单文件 JSON 供本地索引与交互"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        jobs = self.get_all_jobs()
        counselors = self.get_all_counselor_jobs()

        # 读取央企名录
        ent_rows = []
        with self._get_connection() as conn:
            try:
                ent_rows = [dict(r) for r in conn.execute("SELECT * FROM central_enterprises ORDER BY id ASC").fetchall()]
            except sqlite3.OperationalError:
                pass

        data = {
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_jobs": len(jobs),
            "total_enterprises": len(ent_rows),
            "total_counselors": len(counselors),
            "jobs": jobs,
            "enterprises": ent_rows,
            "counselor_jobs": counselors
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📦 已将本地全量数据导出至: {os.path.abspath(output_path)}")
