import pytest
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase

def test_counselor_adapter():
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 13:15:00"
    jobs = adapter.fetch_counselor_jobs(province="浙江", city="杭州", batch_timestamp=timestamp)
    
    assert len(jobs) > 0
    for j in jobs:
        assert j.province == "浙江"
        assert j.city == "杭州"
        assert j.fetched_at == timestamp

def test_counselor_db_saving(tmp_path):
    db_file = str(tmp_path / "test_jobhunter.db")
    db = JobDatabase(db_path=db_file)
    
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 13:15:00"
    jobs = adapter.fetch_counselor_jobs(province="浙江", city="杭州", batch_timestamp=timestamp)
    
    saved_count = db.save_counselor_jobs(jobs, batch_timestamp=timestamp)
    assert saved_count == len(jobs)
    
    db_counselors = db.get_all_counselor_jobs()
    assert len(db_counselors) == saved_count
    for c in db_counselors:
        assert c["fetched_at"] == timestamp
