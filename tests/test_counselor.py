import pytest
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase

def test_nationwide_34_provinces_coverage():
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 13:27:00"
    all_anns = adapter.fetch_university_counselor_announcements(province="all", city="all", batch_timestamp=timestamp)
    
    provinces_found = set([a.province for a in all_anns])
    # 验证数据库中涵盖全国的主要省份
    assert len(provinces_found) >= 30
    assert "北京" in provinces_found
    assert "上海" in provinces_found
    assert "四川" in provinces_found
    assert "新疆" in provinces_found

def test_counselor_announcements_db_saving(tmp_path):
    db_file = str(tmp_path / "test_jobhunter.db")
    db = JobDatabase(db_path=db_file)
    
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 13:27:00"
    anns = adapter.fetch_university_counselor_announcements(province="all", city="all", batch_timestamp=timestamp)
    
    saved_count = db.save_counselor_announcements(anns, batch_timestamp=timestamp)
    assert saved_count == len(anns)
    
    db_anns = db.get_all_counselor_announcements()
    assert len(db_anns) == saved_count
