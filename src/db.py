import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from src.models import JobItem, UniversityCounselorAnnouncement

class JobDatabase:
    """本地 SQLite 岗位、央企与高校辅导员招聘公告持久化数据库类"""

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
            try:
                conn.execute("SELECT requirements_json FROM jobs LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute("DROP TABLE IF EXISTS jobs")

            # 岗位表
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

            # 高校辅导员招聘公告表 (带批次时间戳)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS university_counselor_announcements (
                id TEXT PRIMARY KEY,
                university TEXT NOT NULL,
                university_level TEXT,
                province TEXT NOT NULL,
                city TEXT NOT NULL,
                has_announcement INTEGER,
                announcement_status TEXT,
                announcement_title TEXT,
                publish_date TEXT,
                announcement_url TEXT,
                requirements_summary TEXT,
                fetched_at TEXT,
                created_at TEXT,
                source TEXT DEFAULT 'unknown',
                verified INTEGER DEFAULT 0
            )
            """)

            # 存量数据库增量升级:安全补充新列 (保留已有数据,不重建表)
            for col, ddl in (
                ("source", "ALTER TABLE university_counselor_announcements ADD COLUMN source TEXT DEFAULT 'unknown'"),
                ("verified", "ALTER TABLE university_counselor_announcements ADD COLUMN verified INTEGER DEFAULT 0"),
            ):
                try:
                    conn.execute(f"SELECT {col} FROM university_counselor_announcements LIMIT 1")
                except sqlite3.OperationalError:
                    conn.execute(ddl)
            conn.commit()

    def save_jobs(self, jobs: List[JobItem], batch_timestamp: str = None) -> int:
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

    def save_counselor_announcements(self, anns: List[UniversityCounselorAnnouncement], batch_timestamp: str = None) -> int:
        """保存高校辅导员招聘公告记录，打上统一批次时间戳"""
        if not batch_timestamp:
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            for ann in anns:
                fetched_at = ann.fetched_at or batch_timestamp

                conn.execute("""
                INSERT INTO university_counselor_announcements (
                    id, university, university_level, province, city, has_announcement,
                    announcement_status, announcement_title, publish_date, announcement_url,
                    requirements_summary, fetched_at, created_at, source, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    announcement_status=excluded.announcement_status,
                    announcement_title=excluded.announcement_title,
                    publish_date=excluded.publish_date,
                    announcement_url=excluded.announcement_url,
                    fetched_at=excluded.fetched_at,
                    source=excluded.source,
                    verified=excluded.verified
                """, (
                    ann.id, ann.university, ann.university_level, ann.province, ann.city,
                    1 if ann.has_announcement else 0, ann.announcement_status, ann.announcement_title,
                    ann.publish_date, ann.announcement_url, ann.requirements_summary, fetched_at,
                    ann.source, 1 if ann.verified else 0
                ))
            conn.commit()

        self.export_to_json()
        return len(anns)

    def get_all_jobs(self) -> List[Dict]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY fetched_at DESC, match_score DESC").fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['requirements'] = json.loads(item['requirements_json']) if item['requirements_json'] else []
                item['tags'] = json.loads(item['tags_json']) if item['tags_json'] else []
                result.append(item)
            return result

    def get_all_counselor_announcements(self) -> List[Dict]:
        """获取所有高校辅导员招聘公告记录"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM university_counselor_announcements ORDER BY fetched_at DESC, id ASC").fetchall()
            return [dict(row) for row in rows]

    def export_to_json(self, output_path: str = "output/data.json"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        jobs = self.get_all_jobs()
        counselor_anns = self.get_all_counselor_announcements()

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
            "total_counselor_announcements": len(counselor_anns),
            "jobs": jobs,
            "enterprises": ent_rows,
            "counselor_announcements": counselor_anns
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📦 已将本地全量数据导出至: {os.path.abspath(output_path)}")
