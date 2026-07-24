import pytest
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase

def test_counselor_announcements_adapter():
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 13:20:00"
    anns = adapter.fetch_university_counselor_announcements(province="浙江", city="杭州", batch_timestamp=timestamp)
    
    assert len(anns) > 0
    for a in anns:
        assert a.province == "浙江"
        assert a.city == "杭州"
        assert a.fetched_at == timestamp
        assert a.announcement_url.startswith("http")

def test_counselor_announcements_db_saving(tmp_path):
    db_file = str(tmp_path / "test_jobhunter.db")
    db = JobDatabase(db_path=db_file)
    
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 13:20:00"
    anns = adapter.fetch_university_counselor_announcements(province="浙江", city="杭州", batch_timestamp=timestamp)
    
    saved_count = db.save_counselor_announcements(anns, batch_timestamp=timestamp)
    assert saved_count == len(anns)
    
    db_anns = db.get_all_counselor_announcements()
    assert len(db_anns) == saved_count
    for a in db_anns:
        assert a["fetched_at"] == timestamp
        assert "announcement_title" in a
