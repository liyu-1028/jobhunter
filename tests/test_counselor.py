import pytest
from src.adapters.counselor_adapter import CounselorJobAdapter
from src.db import JobDatabase

def test_baidu_search_snippets_fetch():
    adapter = CounselorJobAdapter()
    snippets = adapter.fetch_search_snippets(province="安徽", city="芜湖")
    assert len(snippets) > 0
    assert "title" in snippets[0]
    assert "snippet" in snippets[0]

def test_counselor_announcements_anhui_wuhu_precision():
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 14:03:00"
    anns = adapter.fetch_university_counselor_announcements(province="安徽", city="芜湖", batch_timestamp=timestamp)
    
    assert len(anns) >= 4
    universities = [item.university for item in anns]
    assert "安徽师范大学" in universities
    assert "安徽工程大学" in universities
    assert "皖南医学院" in universities
    
    for item in anns:
        assert item.city in ["芜湖", "all"] or "芜湖" in item.city

def test_counselor_announcements_db_saving(tmp_path):
    db_file = str(tmp_path / "test_jobhunter.db")
    db = JobDatabase(db_path=db_file)
    
    adapter = CounselorJobAdapter()
    timestamp = "2026-07-24 14:03:00"
    anns = adapter.fetch_university_counselor_announcements(province="安徽", city="芜湖", batch_timestamp=timestamp)
    
    saved_count = db.save_counselor_announcements(anns, batch_timestamp=timestamp)
    assert saved_count == len(anns)
    
    db_anns = db.get_all_counselor_announcements()
    assert len(db_anns) == saved_count
